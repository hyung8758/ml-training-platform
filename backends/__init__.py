# canonical Backend 이름을 최소 Runner 구현으로 연결한다.
# Job 호환 관계는 이 코드가 아니라 capabilities.yaml에서 관리한다.

from backends.base import BackendRunner


def load_backend_runner(backend_name: str) -> BackendRunner:
    """지원하는 Backend 이름에 대응하는 Runner 인스턴스를 반환한다."""
    if backend_name == "espnet":
        from backends.espnet.runner import Runner
    elif backend_name == "ms_swift":
        from backends.ms_swift.runner import Runner
    elif backend_name == "llama_factory":
        from backends.llama_factory.runner import Runner
    elif backend_name == "lightning":
        from backends.lightning.runner import Runner
    else:
        raise ValueError(f"Backend Runner를 찾을 수 없습니다: {backend_name}")
    return Runner()
