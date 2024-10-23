def make_printv(verbose: bool):
    def print_v(*args, **kwargs):
        if verbose:
            kwargs["flush"] = True
            print(*args, **kwargs)
        else:
            pass
    return print_v

if __name__ == "__main__":
    print_v = make_printv(True)
    print_v("Hello, world!")