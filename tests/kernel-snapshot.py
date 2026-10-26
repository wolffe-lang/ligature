#!/usr/bin/env python3
"""Nonexecuting structural snapshot with a guard against the inherited run default."""
import pathlib,runpy,subprocess
R=pathlib.Path(__file__).resolve().parent.parent

def snapshot(path,execute=False):
    assert execute is False, 'high-half ELF execution forbidden'
    path=pathlib.Path(path).resolve()
    function=runpy.run_path(str(R/'tools/differ'))['snapshot']
    class Guard:
        CompletedProcess=subprocess.CompletedProcess
        @staticmethod
        def run(args,*positional,**keywords):
            assert pathlib.Path(args[0]).resolve()!=path, 'high-half ELF execution forbidden'
            return subprocess.run(args,*positional,**keywords)
    function.__globals__['subprocess']=Guard
    return function(path,execute=False)
