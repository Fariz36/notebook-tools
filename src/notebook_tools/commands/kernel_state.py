from notebook_tools.runtime.inspect import run_json_probe


def run(notebook, request):
    code = (
        "def _nt_probe():\n"
        "    import os, sys\n"
        "    return {'ok': True, 'python_version': sys.version, 'working_directory': os.getcwd(), 'package_context': None, 'memory_stats': None, 'kernel_availability_status': 'ready'}\n"
        "print(__import__('json').dumps(_nt_probe()))\n"
        "del _nt_probe"
    )
    result = run_json_probe(request, code)
    result["data"]["session_metadata"] = {"session_id": result["kernel_session_id"]}
    return result
