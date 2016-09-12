import mongomock
from nose.tools import assert_true
from coilstring.coilstring import CoilString
import time
from datetime import datetime


class TestCoilString:

    def setUp(self):
        self._db = mongomock.MongoClient().db.collection
        self._cs = CoilString('device1', 'Y')
        self._cs._db = self._db

    def test_add_start(self):
        d_id = self._cs._add_start_entry()
        assert_true(d_id)

    def test_add_stop(self):
        d_id = self._cs._add_start_entry()
        assert_true(d_id)
        time.sleep(1)
        doc = self._cs._add_stop_entry()
        assert_true(doc.get('_id') == d_id)
        assert_true(doc.get('start'))
        assert_true(doc.get('stop'))
        assert_true(doc.get('duration'))

    def test_get_bday(self):
        assert_true(self._cs.bday < datetime.utcnow())

    def test_get_rest_seconds(self):
        self._cs._add_start_entry()
        time.sleep(5)
        self._cs._add_stop_entry()
        seconds = self._cs.total_seconds_rested
        assert_true(seconds >= 5)

    def test_get_percentage(self):
        self._cs._add_start_entry()
        time.sleep(5)
        self._cs._add_stop_entry()
        assert_true(self._cs.report_rest_percentage() >= 50)

    def test_rest_thread(self):
        self._cs.rest()

