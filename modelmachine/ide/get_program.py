from modelmachine.cpu import CPU_LIST, AbstractCPU


def get_cpu(source, protect_memory) -> AbstractCPU:
    """Return empty cpu or raise the ValueError."""
    arch = source[0].strip()
    if arch in CPU_LIST:
        return CPU_LIST[arch](protect_memory)

    msg = f"Unexpected arch (found in first line): {arch}"
    raise ValueError(msg)


def get_program(filename, protect_memory) -> AbstractCPU:
    """Read model machine program."""
    with open(filename) as source_file:
        source = source_file.readlines()
        cpu = get_cpu(source, protect_memory)
        cpu.load_program(source)
        return cpu
