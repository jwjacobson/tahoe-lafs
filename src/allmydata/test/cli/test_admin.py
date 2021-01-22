import json
from io import (
    BytesIO,
    StringIO,
)

from twisted.python.usage import (
    UsageError,
)
from twisted.python.filepath import (
    FilePath,
)

from allmydata.scripts.admin import (
    AdminCommand,
    AddGridManagerCertOptions,
    add_grid_manager_cert,
)
from allmydata.scripts.runner import (
    Options,
)
from ..common import (
    SyncTestCase,
)


fake_cert = {
    "certificate": "{\"expires\":1601687822,\"public_key\":\"pub-v0-cbq6hcf3pxcz6ouoafrbktmkixkeuywpcpbcomzd3lqbkq4nmfga\",\"version\":1}",
    "signature": "fvjd3uvvupf2v6tnvkwjd473u3m3inyqkwiclhp7balmchkmn3px5pei3qyfjnhymq4cjcwvbpqmcwwnwswdtrfkpnlaxuih2zbdmda"
}


class AddCertificateOptions(SyncTestCase):
    """
    Tests for 'tahoe admin add-grid-manager-cert' option validation
    """

    def setUp(self):
        self.tahoe = Options()
        return super(AddCertificateOptions, self).setUp()

    def test_parse_no_data(self):
        """
        When no data is passed to stdin an error is produced
        """
        self.tahoe.stdin = BytesIO(b"")
        self.tahoe.stderr = BytesIO()  # suppress message

        with self.assertRaises(UsageError) as ctx:
            self.tahoe.parseOptions(
                [
                    "admin", "add-grid-manager-cert",
                    "--name", "random-name",
                    "--filename", "-",
                ]
            )

        self.assertIn(
            "Reading certificate from stdin failed",
            str(ctx.exception)
        )

    def test_read_cert_file(self):
        """
        A certificate can be read from a file
        """
        tmp = self.mktemp()
        with open(tmp, "w") as f:
            json.dump(fake_cert, f)

        # certificate should be loaded
        o = self.tahoe.parseOptions(
            [
                "admin", "add-grid-manager-cert",
                "--name", "random-name",
                "--filename", tmp,
            ]
        )
        opts = self.tahoe.subOptions.subOptions
        self.assertEqual(
            fake_cert,
            opts.certificate_data
        )

    def test_bad_certificate(self):
        """
        Unparseable data produces an error
        """
        self.tahoe.stdin = BytesIO(b"{}")
        self.tahoe.stderr = BytesIO()  # suppress message

        with self.assertRaises(UsageError) as ctx:
            self.tahoe.parseOptions(
                [
                    "admin", "add-grid-manager-cert",
                    "--name", "random-name",
                    "--filename", "-",
                ]
            )

        self.assertIn(
            "Grid Manager certificate must contain",
            str(ctx.exception)
        )


class AddCertificateCommand(SyncTestCase):
    """
    Tests for 'tahoe admin add-grid-manager-cert' operation
    """

    def setUp(self):
        self.tahoe = Options()
        self.node_path = FilePath(self.mktemp())
        self.node_path.makedirs()
        with self.node_path.child("tahoe.cfg").open("w") as f:
            f.write("# minimal test config\n")
        return super(AddCertificateCommand, self).setUp()

    def test_add_one(self):
        """
        Adding a certificate succeeds
        """
        self.tahoe.stdin = BytesIO(json.dumps(fake_cert))
        self.tahoe.stderr = BytesIO()
        self.tahoe.parseOptions(
            [
                "--node-directory", self.node_path.path,
                "admin", "add-grid-manager-cert",
                "--name", "zero",
                "--filename", "-",
            ]
        )
        rc = add_grid_manager_cert(self.tahoe.subOptions.subOptions)

        self.assertEqual(rc, 0)
        self.assertEqual(
            {"zero.cert", "tahoe.cfg"},
            set(self.node_path.listdir())
        )
        self.assertIn(
            "There are now 1 certificates",
            self.tahoe.stderr.getvalue()
        )

    def test_add_two(self):
        """
        An error message is produced when adding a certificate with a
        duplicate name.
        """
        self.tahoe.stdin = BytesIO(json.dumps(fake_cert))
        self.tahoe.stderr = BytesIO()
        self.tahoe.parseOptions(
            [
                "--node-directory", self.node_path.path,
                "admin", "add-grid-manager-cert",
                "--name", "zero",
                "--filename", "-",
            ]
        )
        rc = add_grid_manager_cert(self.tahoe.subOptions.subOptions)
        self.assertEqual(rc, 0)

        self.tahoe.stdin = BytesIO(json.dumps(fake_cert))
        self.tahoe.parseOptions(
            [
                "--node-directory", self.node_path.path,
                "admin", "add-grid-manager-cert",
                "--name", "zero",
                "--filename", "-",
            ]
        )
        rc = add_grid_manager_cert(self.tahoe.subOptions.subOptions)
        self.assertEqual(rc, 1)
        self.assertIn(
            "Already have certificate for 'zero'",
            self.tahoe.stderr.getvalue()
        )
