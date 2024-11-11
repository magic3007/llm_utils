# When setting configurations, a hierarchical structure is adopted to ensure flexibility and coverage.
# 1. The default value in the code.
# 1. Environment Variables. These are system-level settings, typically used to define global configurations, but can be overridden by configurations at other levels.
# 2. YAML File Specification. This is a more specific configuration method, usually used to define project or application-level configurations. Settings in the YAML file can override the same settings in the environment variables.
# 3. Command Line Specification. This is the most specific configuration method, usually used to temporarily override settings at other levels. Command line arguments can override settings in the YAML file and environment variables.
# You can copy this file to create your own config.

import argparse
import os
import yaml
import os.path as osp

from traitlets import Bool, Int, Unicode, Float

# See https://traitlets.readthedocs.io/en/stable/using_traitlets.html
from traitlets.config import Configurable


from io import TextIOWrapper
from types import *
from typing import *


def _get_env(
    option_name: str,
    default_value: Union[bool, int, str, float],
) -> Union[bool, int, str, float]:
    env_name = option_name.upper()
    v = os.getenv(env_name, str(default_value))
    if type(default_value) == int:
        return int(v)
    elif type(default_value) == bool:
        return v.lower() == "true"
    elif type(default_value) == float:
        return float(v)
    else:
        return v




class Parser(argparse.ArgumentParser):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def error(self, message):
        raise Exception(f"Error: {message}\n")

class Config(Configurable):
    name_prefix: str = "llmutils"
    env_prefix: str = (
        f"{name_prefix.upper()}_"  # prefix for environment variables, you can override it in your derived class
    )


    llm_provider = Unicode(
        _get_env(env_prefix + "llm_provider", "azure"),
        help="The LiteLLM API Type. See https://docs.litellm.ai/docs/",
    ).tag(config=True)

    llm_model = Unicode(
        _get_env(env_prefix + "llm_model", "gpt-4o"), help="The LLM model", config=True
    )

    llm_max_token = Int(
        _get_env(env_prefix + "llm_max_token", 1000), help="Maximum number of tokens"
    ).tag(config=True)

    llm_temperature = Float(
        _get_env(env_prefix + "llm_temperature", 0.1), help="LLM temperature"
    ).tag(config=True)

    max_attempts = Int(
        _get_env(env_prefix + "max_attempts", 5), help="Maximum number of attempts"
    ).tag(config=True)

    debug = Bool(_get_env(env_prefix + "debug", False), help="Log LLM calls").tag(config=True)

    verbose = Bool(_get_env(env_prefix + "verbose", False), help="Verbose").tag(config=True)

    log = Unicode(_get_env(env_prefix + "log", "log.yaml"), help="The log file").tag(
        config=True
    )

    input_path = Unicode(
        _get_env(env_prefix + "input_path", "input.json"),
        allow_none=True,
        help="The input json file",
    ).tag(config=True)

    output_dir = Unicode(
        _get_env(env_prefix + "output_dir", "output_data"),
        allow_none=True,
        help="The output dir",
    ).tag(config=True)

    override = Bool(
        _get_env(env_prefix + "override", False),
        help="Whether override the existing result in in the output json file",
    ).tag(config=True)

    nthreads = Int(
        _get_env(env_prefix + "nthreads", 1),
        help="number of threads",
    ).tag(config=True)

    # can be configured by yaml file and command lines
    _user_configurable = [
        llm_provider,
        llm_model,
        llm_max_token,
        llm_temperature,
        max_attempts,
        debug,
        log,
        input_path,
        output_dir,
        override,
        nthreads,
        verbose
    ]

    def to_json(self) -> Dict[str, Union[int, str, bool]]:
        """Serialize the object to a JSON string."""
        return {
            "llm_provider": self.llm_provider,
            "llm_model": self.llm_model,
            "llm_max_token": self.llm_max_token,
            "llm_temperature": self.llm_temperature,
            "max_attempts": self.max_attempts,
            "debug": self.debug,
            "log": self.log,
            "input_path": self.input_path,
            "output_dir": self.output_dir,
            "override": self.override,
            "nthreads": self.nthreads,
            "verbose": self.verbose,
        }

    def to_pretty_str(self):
        return "\n".join([f"{k:30} {v}" for k, v in self.to_json().items()])

    def _parser(self):
        parser = Parser(add_help=False)
        # (Jing) I don't know why traitlets.Float needs to be accessed once before it can appear in _trait_values.
        _ = self.llm_temperature
        for trait in self._user_configurable:
            name = f"--{trait.name}"
            value = self._trait_values[trait.name]
            t = type(value)
            if t == bool:
                parser.add_argument(name, default=value, action="store_true")
            else:
                parser.add_argument(name, default=value, type=t)

        return parser

    def _yaml_parser(self):
        parser = argparse.ArgumentParser(description="YAML Config", add_help=False)
        parser.add_argument(
            "-c",
            "--config_yaml",
            default=None,
            type=str,
            metavar="FILE",
            help="YAML config file specifying arguments",
        )
        return parser

    def parse_user_flags(self, argv: List[str]) -> None:
        args, remain = self._yaml_parser().parse_known_args(argv)
        main_parser = self._parser()
        if args.config_yaml:
            with open(args.config_yaml, "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f)
                # override the the default value for main parser
                main_parser.set_defaults(**cfg)

        # The main arg parser re-parses  the args, the usual
        # defaults will have been overridden if config file specified.
        args, unknown_args = main_parser.parse_known_args(remain)

        for x in self._user_configurable:
            self.set_trait(x.name, getattr(args, x.name))

        return unknown_args

    def user_flags_help(self) -> str:
        return "\n".join(
            [
                self.class_get_trait_help(x, self).replace("Config.", "")
                for x in self._user_configurable
            ]
        )

    def user_flags(self) -> str:
        return "\n".join(
            [
                f"  --{x.name:30} {self._trait_values[x.name]}"
                for x in self._user_configurable
            ]
        )

    def parse_only_user_flags(self, args: List[str]) -> Union[bool, str]:
        try:
            unknown = self.parse_user_flags(args)
            if unknown:
                return (
                    f"Unrecognized arguments: {' '.join(unknown)}\n\n"
                    + f"{self.name_prefix} arguments:\n\n{self.user_flags_help()}"
                )
            return True, self.user_flags()
        except Exception as e:
            return False, str(e) + f"\n{self.name_prefix} arguments:\n\n{self.user_flags_help()}"

    def get_module_whitelist(self) -> str:
        if self.module_whitelist == "":
            file_path = os.path.join(os.path.dirname(__file__), f"module_whitelist.txt")
        else:
            file_path = self.module_whitelist

        with open(file_path, "r") as file:
            return [module.rstrip() for module in file if module.rstrip() != ""]


config: Config = Config()

if __name__ == "__main__":
    import sys
    rv, err = config.parse_only_user_flags(sys.argv[1:])
    if rv is False:
        print(err)
    else:
        print(f""" Starting run with the following parameters: {config.to_pretty_str()}""")
