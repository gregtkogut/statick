"""Apply GroovyLint tool and gather results."""

import json
import logging
import subprocess
from typing import List, Optional

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.tool_plugin import ToolPlugin


class GroovyLintToolPlugin(ToolPlugin):
    """Apply GroovyLint tool and gather results."""

    def get_name(self) -> str:
        """Get name of tool."""
        return "groovylint"

    def get_file_types(self) -> List[str]:
        """Return a list of file types the plugin can scan."""
        return ["groovy_src"]

    # pylint: disable=too-many-locals
    def process_files(
        self, package: Package, level: str, files: List[str], user_flags: List[str]
    ) -> Optional[List[str]]:
        """Run tool and gather output."""
        print("Derp", flush=True)
        tool_bin = "npm-groovy-lint"
        print("Derp1", flush=True)

        tool_config = ".groovylintrc.json"
        if self.plugin_context:
            user_config = self.plugin_context.config.get_tool_config(
                self.get_name(), level, "config"
            )
        print("Derp2", flush=True)

        if user_config is not None:
            tool_config = user_config
        if self.plugin_context:
            format_file_name = self.plugin_context.resources.get_file(tool_config)
        print("Derp3", flush=True)

        flags: List[str] = []
        if format_file_name is not None:
            flags += ["--config", format_file_name]
        flags += ["--output", "json"]
        flags += user_flags
        print("Derp4", flush=True)

        total_output: List[str] = []
        print("Derp5", flush=True)

        for src in files:
            try:
                print("Derp5.1", flush=True)
                exe = [tool_bin] + flags + ["-f", src]
                print(f"Derp5.11 {exe}", flush=True)
                output = subprocess.check_output(
                    exe,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                    cwd=package.path,
                )
                print("Derp5.2", flush=True)
                total_output.append(output)
                print("Derp5.3", flush=True)
            except subprocess.CalledProcessError as ex:
                # npm-groovy-lint returns 1 on some errors but still has valid output
                print("Derp5.4", flush=True)
                if ex.returncode == 1:
                    total_output.append(ex.output)
                else:
                    logging.warning(
                        "%s failed! Returncode = %d", tool_bin, ex.returncode
                    )
                    logging.warning("%s exception: %s", self.get_name(), ex.output)
                    return None

            except OSError as ex:
                print("Derp5.5", flush=True)
                logging.warning("Couldn't find %s! (%s)", tool_bin, ex)
                return None
        print("Derp6", flush=True)

        for output in total_output:
            logging.debug("%s", output)
        print("Derp7", flush=True)

        return total_output

    # pylint: enable=too-many-locals

    def parse_output(
        self, total_output: List[str], package: Optional[Package] = None
    ) -> List[Issue]:
        """Parse tool output and report issues."""
        issues: List[Issue] = []

        # pylint: disable=too-many-nested-blocks
        for output in total_output:
            lines = output.split("\n")
            for line in lines:
                try:
                    err_dict = json.loads(line)
                    if "files" in err_dict:
                        all_files = err_dict["files"]
                        for file_name in all_files:
                            file_errs = all_files[file_name]
                            if "errors" in file_errs:
                                for issue in file_errs["errors"]:
                                    severity_str = issue["severity"]
                                    severity = "3"
                                    if severity_str == "info":
                                        severity = "1"
                                    elif severity_str == "warning":
                                        severity = "3"
                                    elif severity_str == "error":
                                        severity = "5"
                                    issues.append(
                                        Issue(
                                            file_name,
                                            str(issue["line"]),
                                            self.get_name(),
                                            issue["rule"],
                                            severity,
                                            issue["msg"],
                                            None,
                                        )
                                    )

                except ValueError as ex:
                    logging.warning("ValueError: %s", ex)
        # pylint: enable=too-many-nested-blocks
        return issues
