import platform


def get_platform() -> str:
    """Detects the current operating system platform.

    Returns:
        str:
            Platform name (
            'linux',
            'freebsd',
            'aix',
            'macos',
            'windows',
            'unknown').
    """
    sys_platform = platform.system().lower()
    if sys_platform.startswith('linux'):
        return 'linux'
    if sys_platform.startswith('freebsd'):
        return 'freebsd'
    if sys_platform.startswith('aix'):
        return 'aix'
    if sys_platform.startswith('darwin'):
        return 'macos'
    if sys_platform.startswith('win') or sys_platform.startswith('cygwin'):
        return 'windows'
    return 'unknown'
