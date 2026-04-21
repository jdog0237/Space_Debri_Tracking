import tempfile
import unittest
from pathlib import Path

from model.services import CatalogValidator, DebrisCatalogLoader
from model.exceptions import CatalogValidationException


class TestCatalogLoading(unittest.TestCase):
    def setUp(self) -> None:
        self.loader = DebrisCatalogLoader()
        self.validator = CatalogValidator()

    def _write_tmp(self, content: str) -> str:
        handle = tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="", delete=False)
        try:
            handle.write(content)
            handle.flush()
            return handle.name
        finally:
            handle.close()

    def test_load_valid_catalog_with_id(self) -> None:
        path = self._write_tmp(
            "id,x,y,z,vx,vy,vz\n"
            "A,1,2,3,0.1,0.2,0.3\n"
            "B,-1,-2,-3,-0.1,-0.2,-0.3\n"
        )
        catalog = self.loader.load_from_csv(path)
        self.validator.validate(catalog)
        self.assertEqual(catalog.get_object_count(), 2)

    def test_load_valid_catalog_with_debris_id_alias(self) -> None:
        path = self._write_tmp(
            "debris_id,x,y,z,vx,vy,vz\n"
            "OBJ-1,0,0,0,1,1,1\n"
        )
        catalog = self.loader.load_from_csv(path)
        self.validator.validate(catalog)
        self.assertEqual(catalog.get_objects()[0].debris_id, "OBJ-1")

    def test_missing_required_column_raises(self) -> None:
        path = self._write_tmp("id,x,y,z,vx,vy\nA,1,2,3,0.1,0.2\n")
        with self.assertRaises(CatalogValidationException):
            self.loader.load_from_csv(path)

    def test_non_numeric_value_raises_with_row_context(self) -> None:
        path = self._write_tmp("id,x,y,z,vx,vy,vz\nA,NOPE,2,3,0.1,0.2,0.3\n")
        with self.assertRaises(CatalogValidationException) as ctx:
            self.loader.load_from_csv(path)
        self.assertIn("Row 2", str(ctx.exception))

    def test_duplicate_ids_rejected_by_validator(self) -> None:
        path = self._write_tmp(
            "id,x,y,z,vx,vy,vz\n"
            "A,1,2,3,0.1,0.2,0.3\n"
            "A,4,5,6,0.4,0.5,0.6\n"
        )
        catalog = self.loader.load_from_csv(path)
        with self.assertRaises(CatalogValidationException):
            self.validator.validate(catalog)

    def test_empty_file_header_only_rejected(self) -> None:
        path = self._write_tmp("id,x,y,z,vx,vy,vz\n")
        catalog = self.loader.load_from_csv(path)
        with self.assertRaises(CatalogValidationException):
            self.validator.validate(catalog)


if __name__ == "__main__":
    unittest.main()

