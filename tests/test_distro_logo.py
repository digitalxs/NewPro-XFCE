import os
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "tools" / "set-distro-logo.sh"
FIXTURES = ROOT / "tests" / "fixtures" / "os-release"

STUB = textwrap.dedent("""\
    #!/bin/sh
    # Stub xfconf-query: answers reads from fixtures, logs writes.
    case "$*" in
      *"-c xsettings -p /Net/IconThemeName"*) echo "${STUB_ICON_THEME:-Papirus}" ;;
      *"-c xfce4-panel -l -v"*) cat "$STUB_PLUGINS" ;;
      *" -s "*) echo "$*" >> "$STUB_LOG" ;;
      *) exit 1 ;;
    esac
    """)


class DistroLogoTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        (self.tmp / "bin").mkdir()
        stub = self.tmp / "bin" / "xfconf-query"
        stub.write_text(STUB)
        stub.chmod(0o755)
        self.icons = self.tmp / "icons"
        self.icons.mkdir()
        self.log = self.tmp / "log"
        self.log.touch()
        self.plugins = self.tmp / "plugins"
        self.set_plugins({1: "applicationsmenu", 2: "tasklist"})

    def tearDown(self):
        subprocess.run(["rm", "-rf", str(self.tmp)], check=True)

    def set_plugins(self, plugins):
        self.plugins.write_text("".join(f"/plugins/plugin-{n}  {name}\n"
                                        for n, name in plugins.items()))

    def add_icon(self, filename):
        path = self.icons / "Papirus" / "48x48" / "apps" / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()

    def run_script(self, distro, *args):
        env = dict(os.environ, PATH=f"{self.tmp / 'bin'}:{os.environ['PATH']}",
                   NEWPRO_ICON_DIRS=str(self.icons), STUB_LOG=str(self.log),
                   STUB_PLUGINS=str(self.plugins))
        return subprocess.run(["sh", str(SCRIPT), "--os-release", str(FIXTURES / distro), *args],
                              capture_output=True, text=True, env=env)

    def writes(self):
        return self.log.read_text().splitlines()

    def test_debian_picks_distributor_logo(self):
        self.add_icon("distributor-logo-debian.svg")
        r = self.run_script("debian")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("logo: distributor-logo-debian", r.stdout)
        self.assertEqual(self.writes(), [
            "-c xfce4-panel -p /plugins/plugin-1/button-icon -s distributor-logo-debian"])

    def test_logo_field_wins(self):
        self.add_icon("fedora-logo-icon.png")
        self.add_icon("distributor-logo-fedora.svg")
        r = self.run_script("fedora")
        self.assertIn("logo: fedora-logo-icon", r.stdout)

    def test_quoted_values_and_id_like(self):
        self.add_icon("distributor-logo-ubuntu.svg")
        r = self.run_script("linuxmint")
        self.assertIn("logo: distributor-logo-ubuntu", r.stdout)

    def test_no_match_changes_nothing(self):
        r = self.run_script("void")
        self.assertEqual(r.returncode, 0)
        self.assertIn("no logo found", r.stdout)
        self.assertEqual(self.writes(), [])

    def test_multiple_and_zero_plugins(self):
        self.add_icon("distributor-logo-debian.svg")
        self.set_plugins({1: "applicationsmenu", 4: "clock", 7: "whiskermenu"})
        self.run_script("debian")
        self.assertEqual(self.writes(), [
            "-c xfce4-panel -p /plugins/plugin-1/button-icon -s distributor-logo-debian",
            "-c xfce4-panel -p /plugins/plugin-7/button-icon -s distributor-logo-debian"])
        self.log.write_text("")
        self.set_plugins({4: "clock"})
        r = self.run_script("debian")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(self.writes(), [])

    def test_dry_run_writes_nothing(self):
        self.add_icon("distributor-logo-debian.svg")
        r = self.run_script("debian", "--dry-run")
        self.assertIn("set /plugins/plugin-1/button-icon", r.stdout)
        self.assertEqual(self.writes(), [])

    def test_logo_field_without_suffix(self):
        """Arch: LOGO=archlinux-logo, icon theme ships distributor-logo-archlinux."""
        self.add_icon("distributor-logo-archlinux.svg")
        r = self.run_script("arch")
        self.assertIn("logo: distributor-logo-archlinux", r.stdout)

    def test_known_renames_beat_id_like(self):
        """Mint: ID=linuxmint, icon is distributor-logo-linux-mint; must win over ubuntu."""
        self.add_icon("distributor-logo-linux-mint.svg")
        self.add_icon("distributor-logo-ubuntu.svg")
        r = self.run_script("linuxmint")
        self.assertIn("logo: distributor-logo-linux-mint", r.stdout)

    def test_id_edition_suffix_dropped(self):
        self.add_icon("distributor-logo-opensuse.svg")
        r = self.run_script("opensuse-tumbleweed")
        self.assertIn("logo: distributor-logo-opensuse", r.stdout)

    def test_bad_argument(self):
        r = self.run_script("debian", "--bogus")
        self.assertEqual(r.returncode, 2)


if __name__ == "__main__":
    unittest.main()
