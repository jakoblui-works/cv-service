import asyncio
import os
import shutil
import signal
from pathlib import Path
from tempfile import TemporaryDirectory

STYLE_FILE = Path(__file__).parent / "templates" / "preamble.sty"


class LatexCompileError(Exception):
    pass


async def compile_latex(source: str) -> bytes:
    with TemporaryDirectory() as tmp:
        workdir = Path(tmp)

        (workdir / "main.tex").write_text(source, encoding="utf-8")

        shutil.copy(STYLE_FILE, workdir)

        proc = await asyncio.create_subprocess_exec(
            "latexmk",
            "-xelatex",
            "-interaction=nonstopmode",
            "-halt-on-error",
            "-no-shell-escape",
            "main.tex",
            cwd=workdir,
            start_new_session=True,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        try:
            async with asyncio.timeout(30):
                output, _ = await proc.communicate()
        except TimeoutError:
            os.killpg(proc.pid, signal.SIGKILL)
            await proc.wait()
            raise LatexCompileError("timed out") from None

        if proc.returncode != 0:
            tail = output.decode(errors="replace")[-2000:]
            raise LatexCompileError(f"latexmk exited with {proc.returncode}:\n{tail}")

        pdf_bytes = (workdir / "main.pdf").read_bytes()
        return pdf_bytes
