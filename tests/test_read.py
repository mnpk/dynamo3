""" Test the read functions of Dynamo """
from __future__ import unicode_literals

from six.moves import xrange as _xrange  # pylint: disable=F0401

from . import BaseSystemTest, is_number
from dynamo3 import STRING, NUMBER, DynamoKey, LocalIndex, GlobalIndex, TOTAL
from dynamo3.result import Result, GetResultSet
from mock import MagicMock


class TestQuery(BaseSystemTest):

    """ Tests for table queries """

    def make_table(self):
        """ Convenience method for making a table """
        hash_key = DynamoKey('id')
        range_key = DynamoKey('num', data_type=NUMBER)
        self.dynamo.create_table('foobar', hash_key=hash_key,
                                 range_key=range_key)

    def test_hash(self):
        """ Can query on the hash key """
        hash_key = DynamoKey('id')
        self.dynamo.create_table('foobar', hash_key)
        self.dynamo.put_item('foobar', {'id': 'a'})
        results = self.dynamo.query('foobar', id__eq='a')
        self.assertItemsEqual(list(results), [{'id': 'a'}])

    def test_local_index(self):
        """ Can query on a local index """
        hash_key = DynamoKey('id', data_type=STRING)
        range_key = DynamoKey('num', data_type=NUMBER)
        index_field = DynamoKey('name')
        index = LocalIndex.keys('name-index', index_field)
        self.dynamo.create_table('foobar', hash_key, range_key,
                                 indexes=[index])
        item = {
            'id': 'a',
            'num': 1,
            'name': 'baz',
        }
        self.dynamo.put_item('foobar', item)
        ret = self.dynamo.query('foobar', id__eq='a', name__eq='baz',
                                index='name-index')
        self.assertItemsEqual(list(ret), [item])

    def test_global_index(self):
        """ Can query on a global index """
        hash_key = DynamoKey('id', data_type=STRING)
        index_field = DynamoKey('name')
        index = GlobalIndex.all('name-index', index_field)
        self.dynamo.create_table('foobar', hash_key, global_indexes=[index])
        item = {
            'id': 'a',
            'name': 'baz',
        }
        self.dynamo.put_item('foobar', item)
        ret = self.dynamo.query('foobar', name__eq='baz',
                                index='name-index',
                                filter={'id__eq': 'a'})
        self.assertItemsEqual(list(ret), [item])

    def test_attributes(self):
        """ Can select only certain attributes """
        hash_key = DynamoKey('id')
        self.dynamo.create_table('foobar', hash_key)
        item = {
            'id': 'a',
            'foo': 'bar',
        }
        self.dynamo.put_item('foobar', item)
        results = self.dynamo.query('foobar', attributes=['id'], id__eq='a')
        self.assertItemsEqual(list(results), [{'id': 'a'}])

    def test_order_desc(self):
        """ Can sort the results in descending order """
        self.make_table()
        with self.dynamo.batch_write('foobar') as batch:
            for i in _xrange(3):
                batch.put({'id': 'a', 'num': i})
        ret = self.dynamo.query('foobar', attributes=['num'], id__eq='a',
                                desc=True)
        self.assertEqual(list(ret), [{'num': i} for i in range(2, -1, -1)])

    def test_limit(self):
        """ Can limit the number of query results """
        self.make_table()
        with self.dynamo.batch_write('foobar') as batch:
            for i in _xrange(3):
                batch.put({'id': 'a', 'num': i})
        ret = self.dynamo.query('foobar', id__eq='a', limit=1)
        self.assertEqual(len(list(ret)), 1)

    def test_count(self):
        """ Can count items instead of returning the actual items """
        self.make_table()
        with self.dynamo.batch_write('foobar') as batch:
            for i in _xrange(3):
                batch.put({'id': 'a', 'num': i})
        ret = self.dynamo.query('foobar', count=True, id__eq='a')
        self.assertEqual(ret, 3)

    def test_capacity(self):
        """ Can return consumed capacity """
        self.make_table()
        self.dynamo.put_item('foobar', {'id': 'a', 'num': 1})
        ret = self.dynamo.query('foobar', return_capacity=TOTAL, id__eq='a')
        list(ret)
        self.assertTrue(is_number(ret.capacity))
        self.assertTrue(is_number(ret.table_capacity))
        self.assertTrue(isinstance(ret.indexes, dict))
        self.assertTrue(isinstance(ret.global_indexes, dict))

    def test_eq(self):
        """ Can query with EQ constraint """
        self.make_table()
        item = {'id': 'a', 'num': 1}
        self.dynamo.put_item('foobar', item)
        self.dynamo.put_item('foobar', {'id': 'a', 'num': 2})
        ret = self.dynamo.query('foobar', id__eq='a', num__eq=1)
        self.assertItemsEqual(list(ret), [item])

    def test_le(self):
        """ Can query with <= constraint """
        self.make_table()
        item = {'id': 'a', 'num': 1}
        self.dynamo.put_item('foobar', item)
        self.dynamo.put_item('foobar', {'id': 'a', 'num': 2})
        ret = self.dynamo.query('foobar', id__eq='a', num__le=1)
        self.assertItemsEqual(list(ret), [item])

    def test_lt(self):
        """ Can query with < constraint """
        self.make_table()
        item = {'id': 'a', 'num': 1}
        self.dynamo.put_item('foobar', item)
        self.dynamo.put_item('foobar', {'id': 'a', 'num': 2})
        ret = self.dynamo.query('foobar', id__eq='a', num__lt=2)
        self.assertItemsEqual(list(ret), [item])

    def test_ge(self):
        """ Can query with >= constraint """
        self.make_table()
        item = {'id': 'a', 'num': 2}
        self.dynamo.put_item('foobar', {'id': 'a', 'num': 1})
        self.dynamo.put_item('foobar', item)
        ret = self.dynamo.query('foobar', id__eq='a', num__ge=2)
        self.assertItemsEqual(list(ret), [item])

    def test_gt(self):
        """ Can query with > constraint """
        self.make_table()
        item = {'id': 'a', 'num': 2}
        self.dynamo.put_item('foobar', {'id': 'a', 'num': 1})
        self.dynamo.put_item('foobar', item)
        ret = self.dynamo.query('foobar', id__eq='a', num__gt=1)
        self.assertItemsEqual(list(ret), [item])

    def test_beginswith(self):
        """ Can query with 'begins with' constraint """
        hash_key = DynamoKey('id')
        range_key = DynamoKey('name')
        self.dynamo.create_table('foobar', hash_key=hash_key,
                                 range_key=range_key)
        item = {'id': 'a', 'name': 'David'}
        self.dynamo.put_item('foobar', {'id': 'a', 'name': 'Steven'})
        self.dynamo.put_item('foobar', item)
        ret = self.dynamo.query('foobar', id__eq='a', name__beginswith='D')
        self.assertItemsEqual(list(ret), [item])

    def test_between(self):
        """ Can query with 'between' constraint """
        self.make_table()
        item = {'id': 'a', 'num': 2}
        self.dynamo.put_item('foobar', {'id': 'a', 'num': 1})
        self.dynamo.put_item('foobar', item)
        ret = self.dynamo.query('foobar', id__eq='a', num__between=(2, 10))
        self.assertItemsEqual(list(ret), [item])

    def test_bad_query_op(self):
        """ Malformed query keyword raises error """
        self.make_table()
        with self.assertRaises(TypeError):
            self.dynamo.query('foobar', id__eq='a', num_lt=3)

    def test_filter(self):
        """ Query can filter returned results """
        self.make_table()
        self.dynamo.put_item('foobar', {'id': 'a', 'num': 1, 'a': 'a'})
        self.dynamo.put_item('foobar', {'id': 'a', 'num': 2, 'b': 'b'})
        results = self.dynamo.query('foobar', filter={'a__eq': 'a'},
                                    id__eq='a')
        self.assertItemsEqual(list(results), [{'id': 'a', 'num': 1, 'a': 'a'}])

    def test_filter_and(self):
        """ Can 'and' the filter arguments """
        self.make_table()
        a = {'id': 'a', 'num': 1, 'a': 'a', 'b': 'a'}
        self.dynamo.put_item('foobar', a)
        b = {'id': 'a', 'num': 2, 'a': 'a', 'b': 'b'}
        self.dynamo.put_item('foobar', b)
        results = self.dynamo.query('foobar',
                                    filter={'a__eq': 'a', 'b__eq': 'a'},
                                    id__eq='a')
        self.assertItemsEqual(list(results), [a])

    def test_filter_or(self):
        """ Can 'or' the filter arguments """
        self.make_table()
        a = {'id': 'a', 'num': 1, 'a': 'a', 'b': 'a'}
        self.dynamo.put_item('foobar', a)
        b = {'id': 'a', 'num': 2, 'a': 'a', 'b': 'b'}
        self.dynamo.put_item('foobar', b)
        results = self.dynamo.query('foobar',
                                    filter={'a__eq': 'a', 'b__eq': 'a'},
                                    filter_or=True,
                                    id__eq='a')
        self.assertItemsEqual(list(results), [a, b])


class TestQuery2(BaseSystemTest):

    """ Tests for the newer query API """

    def make_table(self):
        """ Convenience method for making a table """
        hash_key = DynamoKey('id')
        range_key = DynamoKey('num', data_type=NUMBER)
        self.dynamo.create_table('foobar', hash_key=hash_key,
                                 range_key=range_key)

    def test_hash(self):
        """ Can query on the hash key """
        hash_key = DynamoKey('id')
        self.dynamo.create_table('foobar', hash_key)
        self.dynamo.put_item('foobar', {'id': 'a'})
        results = self.dynamo.query2('foobar', 'id = :id', id='a')
        self.assertItemsEqual(list(results), [{'id': 'a'}])

    def test_local_index(self):
        """ Can query on a local index """
        hash_key = DynamoKey('id', data_type=STRING)
        range_key = DynamoKey('num', data_type=NUMBER)
        index_field = DynamoKey('name')
        index = LocalIndex.keys('name-index', index_field)
        self.dynamo.create_table('foobar', hash_key, range_key,
                                 indexes=[index])
        item = {
            'id': 'a',
            'num': 1,
            'name': 'baz',
        }
        self.dynamo.put_item('foobar', item)
        ret = self.dynamo.query2('foobar', 'id = :id and #name = :name',
                                 alias={'#name': 'name'},
                                 index='name-index', id='a', name='baz')
        self.assertItemsEqual(list(ret), [item])

    def test_global_index(self):
        """ Can query on a global index """
        hash_key = DynamoKey('id', data_type=STRING)
        index_field = DynamoKey('name')
        index = GlobalIndex.all('name-index', index_field)
        self.dynamo.create_table('foobar', hash_key, global_indexes=[index])
        item = {
            'id': 'a',
            'name': 'baz',
        }
        self.dynamo.put_item('foobar', item)
        ret = self.dynamo.query2('foobar', '#name = :name',
                                 alias={'#name': 'name'},
                                 index='name-index',
                                 filter='id = :id', id='a', name='baz')
        self.assertItemsEqual(list(ret), [item])

    def test_attributes(self):
        """ Can select only certain attributes """
        hash_key = DynamoKey('id')
        self.dynamo.create_table('foobar', hash_key)
        item = {
            'id': 'a',
            'foo': 'bar',
        }
        self.dynamo.put_item('foobar', item)
        results = self.dynamo.query2('foobar', 'id = :id', attributes='id',
                                     id='a')
        self.assertItemsEqual(list(results), [{'id': 'a'}])

    def test_attributes_list(self):
        """ Can select only certain attributes via list """
        hash_key = DynamoKey('id')
        self.dynamo.create_table('foobar', hash_key)
        item = {
            'id': 'a',
            'foo': 'bar',
        }
        self.dynamo.put_item('foobar', item)
        results = self.dynamo.query2('foobar', 'id = :id', attributes=['id'],
                                     id='a')
        self.assertItemsEqual(list(results), [{'id': 'a'}])

    def test_order_desc(self):
        """ Can sort the results in descending order """
        self.make_table()
        with self.dynamo.batch_write('foobar') as batch:
            for i in _xrange(3):
                batch.put({'id': 'a', 'num': i})
        ret = self.dynamo.query2('foobar', 'id = :id', attributes='num',
                                 desc=True, id='a')
        self.assertEqual(list(ret), [{'num': i} for i in range(2, -1, -1)])

    def test_limit(self):
        """ Can limit the number of query results """
        self.make_table()
        with self.dynamo.batch_write('foobar') as batch:
            for i in _xrange(3):
                batch.put({'id': 'a', 'num': i})
        ret = self.dynamo.query2('foobar', 'id = :id', limit=1, id='a')
        self.assertEqual(len(list(ret)), 1)

    def test_count(self):
        """ Can count items instead of returning the actual items """
        self.make_table()
        with self.dynamo.batch_write('foobar') as batch:
            for i in _xrange(3):
                batch.put({'id': 'a', 'num': i})
        ret = self.dynamo.query2('foobar', 'id = :id', select='COUNT', id='a')
        self.assertEqual(ret['Count'], 3)
        self.assertEqual(ret['ScannedCount'], 3)

    def test_capacity(self):
        """ Can return consumed capacity """
        self.make_table()
        self.dynamo.put_item('foobar', {'id': 'a', 'num': 1})
        ret = self.dynamo.query2('foobar', 'id = :id', return_capacity=TOTAL,
                                 id='a')
        list(ret)
        self.assertTrue(is_number(ret.capacity))
        self.assertTrue(is_number(ret.table_capacity))
        self.assertTrue(isinstance(ret.indexes, dict))
        self.assertTrue(isinstance(ret.global_indexes, dict))

    def test_eq(self):
        """ Can query with EQ constraint """
        self.make_table()
        item = {'id': 'a', 'num': 1}
        self.dynamo.put_item('foobar', item)
        self.dynamo.put_item('foobar', {'id': 'a', 'num': 2})
        ret = self.dynamo.query2('foobar', 'id = :id and num = :num', id='a',
                                 num=1)
        self.assertItemsEqual(list(ret), [item])

    def test_le(self):
        """ Can query with <= constraint """
        self.make_table()
        item = {'id': 'a', 'num': 1}
        self.dynamo.put_item('foobar', item)
        self.dynamo.put_item('foobar', {'id': 'a', 'num': 2})
        ret = self.dynamo.query2('foobar', 'id = :id and num <= :num', id='a',
                                 num=1)
        self.assertItemsEqual(list(ret), [item])

    def test_lt(self):
        """ Can query with < constraint """
        self.make_table()
        item = {'id': 'a', 'num': 1}
        self.dynamo.put_item('foobar', item)
        self.dynamo.put_item('foobar', {'id': 'a', 'num': 2})
        ret = self.dynamo.query2('foobar', 'id = :id and num < :num', id='a',
                                 num=2)
        self.assertItemsEqual(list(ret), [item])

    def test_ge(self):
        """ Can query with >= constraint """
        self.make_table()
        item = {'id': 'a', 'num': 2}
        self.dynamo.put_item('foobar', {'id': 'a', 'num': 1})
        self.dynamo.put_item('foobar', item)
        ret = self.dynamo.query2('foobar', 'id = :id and num >= :num', id='a',
                                 num=2)
        self.assertItemsEqual(list(ret), [item])

    def test_gt(self):
        """ Can query with > constraint """
        self.make_table()
        item = {'id': 'a', 'num': 2}
        self.dynamo.put_item('foobar', {'id': 'a', 'num': 1})
        self.dynamo.put_item('foobar', item)
        ret = self.dynamo.query2('foobar', 'id = :id and num > :num', id='a',
                                 num=1)
        self.assertItemsEqual(list(ret), [item])

    def test_beginswith(self):
        """ Can query with 'begins with' constraint """
        hash_key = DynamoKey('id')
        range_key = DynamoKey('name')
        self.dynamo.create_table('foobar', hash_key=hash_key,
                                 range_key=range_key)
        item = {'id': 'a', 'name': 'David'}
        self.dynamo.put_item('foobar', {'id': 'a', 'name': 'Steven'})
        self.dynamo.put_item('foobar', item)
        ret = self.dynamo.query2('foobar',
                                 'id = :id and begins_with(#name, :name)',
                                 alias={'#name': 'name'}, id='a', name='D')
        self.assertItemsEqual(list(ret), [item])

    def test_between(self):
        """ Can query with 'between' constraint """
        self.make_table()
        item = {'id': 'a', 'num': 2}
        self.dynamo.put_item('foobar', {'id': 'a', 'num': 1})
        self.dynamo.put_item('foobar', item)
        ret = self.dynamo.query2('foobar',
                                 'id = :id and num between :low and :high',
                                 id='a', low=2, high=10)
        self.assertItemsEqual(list(ret), [item])

    def test_no_kwargs(self):
        """ Expression values can be passed in as a dict """
        hash_key = DynamoKey('id')
        self.dynamo.create_table('foobar', hash_key)
        self.dynamo.put_item('foobar', {'id': 'a'})
        results = self.dynamo.query2('foobar', 'id = :id',
                                     expr_values={':id': 'a'})
        self.assertItemsEqual(list(results), [{'id': 'a'}])

    def test_filter(self):
        """ Query can filter returned results """
        self.make_table()
        self.dynamo.put_item('foobar', {'id': 'a', 'num': 1, 'a': 'a'})
        self.dynamo.put_item('foobar', {'id': 'a', 'num': 2, 'b': 'b'})
        results = self.dynamo.query2('foobar', 'id = :id', filter='a = :a',
                                     id='a', a='a')
        self.assertItemsEqual(list(results), [{'id': 'a', 'num': 1, 'a': 'a'}])

    def test_filter_and(self):
        """ Can 'and' the filter arguments """
        self.make_table()
        a = {'id': 'a', 'num': 1, 'a': 'a', 'b': 'a'}
        self.dynamo.put_item('foobar', a)
        b = {'id': 'a', 'num': 2, 'a': 'a', 'b': 'b'}
        self.dynamo.put_item('foobar', b)
        results = self.dynamo.query2('foobar', 'id = :id',
                                     filter='a = :a and b = :b',
                                     id='a', a='a', b='a')
        self.assertItemsEqual(list(results), [a])

    def test_filter_or(self):
        """ Can 'or' the filter arguments """
        self.make_table()
        a = {'id': 'a', 'num': 1, 'a': 'a', 'b': 'a'}
        self.dynamo.put_item('foobar', a)
        b = {'id': 'a', 'num': 2, 'a': 'a', 'b': 'b'}
        self.dynamo.put_item('foobar', b)
        results = self.dynamo.query2('foobar', 'id = :id',
                                     filter='a = :a or b = :b',
                                     id='a', a='a', b='a')
        self.assertItemsEqual(list(results), [a, b])


class TestScan(BaseSystemTest):

    """ Tests for scanning a table """

    def make_table(self):
        """ Convenience method for making a table """
        hash_key = DynamoKey('id')
        self.dynamo.create_table('foobar', hash_key=hash_key)

    def test_attributes(self):
        """ Can select only certain attributes """
        hash_key = DynamoKey('id')
        self.dynamo.create_table('foobar', hash_key)
        item = {
            'id': 'a',
            'foo': 'bar',
        }
        self.dynamo.put_item('foobar', item)
        results = self.dynamo.scan('foobar', attributes=['id'])
        self.assertItemsEqual(list(results), [{'id': 'a'}])

    def test_limit(self):
        """ Can limit the number of scan results """
        self.make_table()
        with self.dynamo.batch_write('foobar') as batch:
            for i in _xrange(3):
                batch.put({'id': str(i)})
        ret = self.dynamo.scan('foobar', limit=1)
        self.assertEqual(len(list(ret)), 1)

    def test_count(self):
        """ Can count items instead of returning the actual items """
        self.make_table()
        with self.dynamo.batch_write('foobar') as batch:
            for i in _xrange(3):
                batch.put({'id': str(i)})
        ret = self.dynamo.scan('foobar', count=True)
        self.assertEqual(ret, 3)

    def test_capacity(self):
        """ Can return consumed capacity """
        self.make_table()
        self.dynamo.put_item('foobar', {'id': 'a'})
        ret = self.dynamo.scan('foobar', return_capacity=TOTAL)
        list(ret)
        self.assertTrue(is_number(ret.capacity))
        self.assertTrue(is_number(ret.table_capacity))
        self.assertTrue(isinstance(ret.indexes, dict))
        self.assertTrue(isinstance(ret.global_indexes, dict))

    def test_eq(self):
        """ Can scan with EQ constraint """
        self.make_table()
        self.dynamo.put_item('foobar', {'id': 'a'})
        self.dynamo.put_item('foobar', {'id': 'b'})
        ret = self.dynamo.scan('foobar', id__eq='a')
        self.assertItemsEqual(list(ret), [{'id': 'a'}])

    def test_ne(self):
        """ Can scan with NE constraint """
        self.make_table()
        self.dynamo.put_item('foobar', {'id': 'a'})
        self.dynamo.put_item('foobar', {'id': 'b'})
        ret = self.dynamo.scan('foobar', id__ne='b')
        self.assertItemsEqual(list(ret), [{'id': 'a'}])

    def test_le(self):
        """ Can scan with <= constraint """
        self.make_table()
        item = {'id': 'a', 'num': 1}
        self.dynamo.put_item('foobar', item)
        self.dynamo.put_item('foobar', {'id': 'b', 'num': 2})
        ret = self.dynamo.scan('foobar', num__le=1)
        self.assertItemsEqual(list(ret), [item])

    def test_lt(self):
        """ Can scan with < constraint """
        self.make_table()
        item = {'id': 'a', 'num': 1}
        self.dynamo.put_item('foobar', item)
        self.dynamo.put_item('foobar', {'id': 'b', 'num': 2})
        ret = list(self.dynamo.scan('foobar', num__lt=2))
        self.assertItemsEqual(ret, [item])

    def test_ge(self):
        """ Can scan with >= constraint """
        self.make_table()
        item = {'id': 'a', 'num': 2}
        self.dynamo.put_item('foobar', {'id': 'b', 'num': 1})
        self.dynamo.put_item('foobar', item)
        ret = self.dynamo.scan('foobar', num__ge=2)
        self.assertItemsEqual(list(ret), [item])

    def test_gt(self):
        """ Can scan with > constraint """
        self.make_table()
        item = {'id': 'a', 'num': 2}
        self.dynamo.put_item('foobar', {'id': 'b', 'num': 1})
        self.dynamo.put_item('foobar', item)
        ret = self.dynamo.scan('foobar', num__gt=1)
        self.assertItemsEqual(list(ret), [item])

    def test_beginswith(self):
        """ Can scan with 'begins with' constraint """
        hash_key = DynamoKey('id')
        self.dynamo.create_table('foobar', hash_key=hash_key)
        item = {'id': 'a', 'name': 'David'}
        self.dynamo.put_item('foobar', {'id': 'b', 'name': 'Steven'})
        self.dynamo.put_item('foobar', item)
        ret = self.dynamo.scan('foobar', name__beginswith='D')
        self.assertItemsEqual(list(ret), [item])

    def test_between(self):
        """ Can scan with 'between' constraint """
        self.make_table()
        item = {'id': 'a', 'num': 2}
        self.dynamo.put_item('foobar', {'id': 'b', 'num': 1})
        self.dynamo.put_item('foobar', item)
        ret = self.dynamo.scan('foobar', num__between=(2, 10))
        self.assertItemsEqual(list(ret), [item])

    def test_in(self):
        """ Can scan with 'in' constraint """
        self.make_table()
        item = {'id': 'a', 'num': 2}
        self.dynamo.put_item('foobar', {'id': 'b', 'num': 1})
        self.dynamo.put_item('foobar', item)
        ret = self.dynamo.scan('foobar', num__in=(2, 3, 4, 5))
        self.assertItemsEqual(list(ret), [item])

    def test_contains(self):
        """ Can scan with 'contains' constraint """
        self.make_table()
        item = {'id': 'a', 'nums': set([1, 2, 3])}
        self.dynamo.put_item('foobar', {'id': 'b', 'nums': set([4, 5, 6])})
        self.dynamo.put_item('foobar', item)
        ret = list(self.dynamo.scan('foobar', nums__contains=2))
        self.assertItemsEqual(ret, [item])

    def test_ncontains(self):
        """ Can scan with 'not contains' constraint """
        self.make_table()
        item = {'id': 'a', 'nums': set([1, 2, 3])}
        self.dynamo.put_item('foobar', {'id': 'b', 'nums': set([4, 5, 6])})
        self.dynamo.put_item('foobar', item)
        ret = list(self.dynamo.scan('foobar', nums__ncontains=4))
        self.assertItemsEqual(ret, [item])

    def test_is_null(self):
        """ Can scan with 'is null' constraint """
        self.make_table()
        item = {'id': 'a'}
        self.dynamo.put_item('foobar', {'id': 'b', 'num': 1})
        self.dynamo.put_item('foobar', item)
        ret = self.dynamo.scan('foobar', num__null=True)
        self.assertItemsEqual(list(ret), [item])

    def test_is_not_null(self):
        """ Can scan with 'is not null' constraint """
        self.make_table()
        item = {'id': 'a', 'num': 1}
        self.dynamo.put_item('foobar', {'id': 'b'})
        self.dynamo.put_item('foobar', item)
        ret = self.dynamo.scan('foobar', num__null=False)
        self.assertItemsEqual(list(ret), [item])

    def test_filter_and(self):
        """ Multiple filter args are ANDed together """
        self.make_table()
        self.dynamo.put_item('foobar', {'id': 'a', 'a': 'a', 'b': 'a'})
        self.dynamo.put_item('foobar', {'id': 'b', 'a': 'a', 'b': 'b'})
        ret = self.dynamo.scan('foobar', a__eq='a', b__eq='a')
        self.assertItemsEqual(list(ret), [{'id': 'a', 'a': 'a', 'b': 'a'}])

    def test_filter_or(self):
        """ Can 'or' the filter arguments """
        self.make_table()
        a = {'id': 'a', 'a': 'a', 'b': 'a'}
        self.dynamo.put_item('foobar', a)
        b = {'id': 'b', 'a': 'a', 'b': 'b'}
        self.dynamo.put_item('foobar', b)
        ret = self.dynamo.scan('foobar', filter_or=True, a__eq='a', b__eq='a')
        self.assertItemsEqual(list(ret), [a, b])


class TestScan2(BaseSystemTest):

    """ Tests for newer scan api """

    def make_table(self):
        """ Convenience method for making a table """
        hash_key = DynamoKey('id')
        self.dynamo.create_table('foobar', hash_key=hash_key)

    def test_attributes(self):
        """ Can select only certain attributes """
        hash_key = DynamoKey('id')
        self.dynamo.create_table('foobar', hash_key)
        item = {
            'id': 'a',
            'foo': 'bar',
        }
        self.dynamo.put_item('foobar', item)
        results = self.dynamo.scan2('foobar', attributes='id')
        self.assertItemsEqual(list(results), [{'id': 'a'}])

    def test_attributes_list(self):
        """ Can select only certain attributes specified by a list """
        hash_key = DynamoKey('id')
        self.dynamo.create_table('foobar', hash_key)
        item = {
            'id': 'a',
            'foo': 'bar',
        }
        self.dynamo.put_item('foobar', item)
        results = self.dynamo.scan2('foobar', attributes=['id'])
        self.assertItemsEqual(list(results), [{'id': 'a'}])

    def test_limit(self):
        """ Can limit the number of scan results """
        self.make_table()
        with self.dynamo.batch_write('foobar') as batch:
            for i in _xrange(3):
                batch.put({'id': str(i)})
        ret = self.dynamo.scan2('foobar', limit=1)
        self.assertEqual(len(list(ret)), 1)

    def test_count(self):
        """ Can count items instead of returning the actual items """
        self.make_table()
        with self.dynamo.batch_write('foobar') as batch:
            for i in _xrange(3):
                batch.put({'id': str(i)})
        ret = self.dynamo.scan2('foobar', select='COUNT')
        self.assertEqual(ret['Count'], 3)
        self.assertEqual(ret['ScannedCount'], 3)

    def test_capacity(self):
        """ Can return consumed capacity """
        self.make_table()
        self.dynamo.put_item('foobar', {'id': 'a'})
        ret = self.dynamo.scan2('foobar', return_capacity=TOTAL)
        list(ret)
        self.assertTrue(is_number(ret.capacity))
        self.assertTrue(is_number(ret.table_capacity))
        self.assertTrue(isinstance(ret.indexes, dict))
        self.assertTrue(isinstance(ret.global_indexes, dict))

    def test_eq(self):
        """ Can scan with EQ constraint """
        self.make_table()
        self.dynamo.put_item('foobar', {'id': 'a'})
        self.dynamo.put_item('foobar', {'id': 'b'})
        ret = self.dynamo.scan2('foobar', filter='id = :id', id='a')
        self.assertItemsEqual(list(ret), [{'id': 'a'}])

    def test_expr_values(self):
        """ Can pass in ExpressionAttributeValues direcly """
        self.make_table()
        self.dynamo.put_item('foobar', {'id': 'a'})
        self.dynamo.put_item('foobar', {'id': 'b'})
        ret = self.dynamo.scan2('foobar', filter='id = :id', expr_values={':id': 'a'})
        self.assertItemsEqual(list(ret), [{'id': 'a'}])

    def test_ne(self):
        """ Can scan with NE constraint """
        self.make_table()
        self.dynamo.put_item('foobar', {'id': 'a'})
        self.dynamo.put_item('foobar', {'id': 'b'})
        ret = self.dynamo.scan2('foobar', filter='id <> :id', id='b')
        self.assertItemsEqual(list(ret), [{'id': 'a'}])

    def test_le(self):
        """ Can scan with <= constraint """
        self.make_table()
        item = {'id': 'a', 'num': 1}
        self.dynamo.put_item('foobar', item)
        self.dynamo.put_item('foobar', {'id': 'b', 'num': 2})
        ret = self.dynamo.scan2('foobar', filter='num <= :num', num=1)
        self.assertItemsEqual(list(ret), [item])

    def test_lt(self):
        """ Can scan with < constraint """
        self.make_table()
        item = {'id': 'a', 'num': 1}
        self.dynamo.put_item('foobar', item)
        self.dynamo.put_item('foobar', {'id': 'b', 'num': 2})
        ret = list(self.dynamo.scan2('foobar', filter='num < :num', num=2))
        self.assertItemsEqual(ret, [item])

    def test_ge(self):
        """ Can scan with >= constraint """
        self.make_table()
        item = {'id': 'a', 'num': 2}
        self.dynamo.put_item('foobar', {'id': 'b', 'num': 1})
        self.dynamo.put_item('foobar', item)
        ret = self.dynamo.scan2('foobar', filter='num >= :num', num=2)
        self.assertItemsEqual(list(ret), [item])

    def test_gt(self):
        """ Can scan with > constraint """
        self.make_table()
        item = {'id': 'a', 'num': 2}
        self.dynamo.put_item('foobar', {'id': 'b', 'num': 1})
        self.dynamo.put_item('foobar', item)
        ret = self.dynamo.scan2('foobar', filter='num > :num', num=1)
        self.assertItemsEqual(list(ret), [item])

    def test_beginswith(self):
        """ Can scan with 'begins with' constraint """
        hash_key = DynamoKey('id')
        self.dynamo.create_table('foobar', hash_key=hash_key)
        item = {'id': 'a', 'name': 'David'}
        self.dynamo.put_item('foobar', {'id': 'b', 'name': 'Steven'})
        self.dynamo.put_item('foobar', item)
        ret = self.dynamo.scan2('foobar', filter='begins_with(#name, :name)',
                                alias={'#name': 'name'}, name='D')
        self.assertItemsEqual(list(ret), [item])

    def test_between(self):
        """ Can scan with 'between' constraint """
        self.make_table()
        item = {'id': 'a', 'num': 2}
        self.dynamo.put_item('foobar', {'id': 'b', 'num': 1})
        self.dynamo.put_item('foobar', item)
        ret = self.dynamo.scan2('foobar', filter='num between :low and :high',
                                low=2, high=10)
        self.assertItemsEqual(list(ret), [item])

    def test_in(self):
        """ Can scan with 'in' constraint """
        self.make_table()
        item = {'id': 'a', 'num': 2}
        self.dynamo.put_item('foobar', {'id': 'b', 'num': 1})
        self.dynamo.put_item('foobar', item)
        ret = self.dynamo.scan2('foobar', filter='num in (:v1, :v2, :v3, :v4)',
                                v1=2, v2=3, v3=4, v4=4)
        self.assertItemsEqual(list(ret), [item])

    def test_contains(self):
        """ Can scan with 'contains' constraint """
        self.make_table()
        item = {'id': 'a', 'nums': set([1, 2, 3])}
        self.dynamo.put_item('foobar', {'id': 'b', 'nums': set([4, 5, 6])})
        self.dynamo.put_item('foobar', item)
        ret = list(self.dynamo.scan2('foobar', filter='contains(nums, :num)', num=2))
        self.assertItemsEqual(ret, [item])

    def test_ncontains(self):
        """ Can scan with 'not contains' constraint """
        self.make_table()
        item = {'id': 'a', 'nums': set([1, 2, 3])}
        self.dynamo.put_item('foobar', {'id': 'b', 'nums': set([4, 5, 6])})
        self.dynamo.put_item('foobar', item)
        ret = list(self.dynamo.scan2('foobar',
                                     filter='not contains(nums, :num)', num=4))
        self.assertItemsEqual(ret, [item])

    def test_is_null(self):
        """ Can scan with 'is null' constraint """
        self.make_table()
        item = {'id': 'a'}
        self.dynamo.put_item('foobar', {'id': 'b', 'num': 1})
        self.dynamo.put_item('foobar', item)
        ret = self.dynamo.scan2('foobar', filter='not attribute_exists(num)')
        self.assertItemsEqual(list(ret), [item])

    def test_is_not_null(self):
        """ Can scan with 'is not null' constraint """
        self.make_table()
        item = {'id': 'a', 'num': 1}
        self.dynamo.put_item('foobar', {'id': 'b'})
        self.dynamo.put_item('foobar', item)
        ret = self.dynamo.scan2('foobar', filter='attribute_exists(num)')
        self.assertItemsEqual(list(ret), [item])

    def test_filter_and(self):
        """ Multiple filter args are ANDed together """
        self.make_table()
        self.dynamo.put_item('foobar', {'id': 'a', 'a': 'a', 'b': 'a'})
        self.dynamo.put_item('foobar', {'id': 'b', 'a': 'a', 'b': 'b'})
        ret = self.dynamo.scan2('foobar', filter='a = :a and b = :b', a='a',
                                b='a')
        self.assertItemsEqual(list(ret), [{'id': 'a', 'a': 'a', 'b': 'a'}])

    def test_filter_or(self):
        """ Can 'or' the filter arguments """
        self.make_table()
        a = {'id': 'a', 'a': 'a', 'b': 'a'}
        self.dynamo.put_item('foobar', a)
        b = {'id': 'b', 'a': 'a', 'b': 'b'}
        self.dynamo.put_item('foobar', b)
        ret = self.dynamo.scan2('foobar', filter='a = :a or b = :b', a='a',
                                b='a')
        self.assertItemsEqual(list(ret), [a, b])

    def test_scan_index(self):
        """ Can scan a global index """
        hash_key = DynamoKey('id', data_type=STRING)
        index_field = DynamoKey('name')
        index = GlobalIndex.all('name-index', index_field)
        self.dynamo.create_table('foobar', hash_key, global_indexes=[index])
        item = {
            'id': 'a',
            'name': 'baz',
        }
        self.dynamo.put_item('foobar', item)
        item2 = {
            'id': 'b',
        }
        self.dynamo.put_item('foobar', item2)
        ret = self.dynamo.scan2('foobar', index='name-index')
        self.assertItemsEqual(list(ret), [item])

    def test_parallel_scan(self):
        """ Can scan a table in segments """
        self.make_table()
        self.dynamo.put_item('foobar', {'id': 'a'})
        self.dynamo.put_item('foobar', {'id': 'b'})
        self.dynamo.put_item('foobar', {'id': 'c'})
        self.dynamo.put_item('foobar', {'id': 'd'})
        ret1 = self.dynamo.scan2('foobar', segment=0, total_segments=2)
        ret2 = self.dynamo.scan2('foobar', segment=1, total_segments=2)
        self.assertItemsEqual(list(ret1) + list(ret2),
                              [{'id': 'a'}, {'id': 'b'},
                               {'id': 'c'}, {'id': 'd'}])


class TestBatchGet(BaseSystemTest):

    """ Tests for the BatchGetItem call """

    def make_table(self):
        """ Convenience method for making a table """
        hash_key = DynamoKey('id')
        self.dynamo.create_table('foobar', hash_key=hash_key)

    def test_get_items(self):
        """ Can get multiple items """
        self.make_table()
        keys = [{'id': 'a'}, {'id': 'b'}]
        self.dynamo.put_item('foobar', keys[0])
        self.dynamo.put_item('foobar', keys[1])
        ret = list(self.dynamo.batch_get('foobar', keys))
        self.assertItemsEqual(ret, keys)

    def test_get_many(self):
        """ Can get many items via paging """
        self.make_table()
        keys = [{'id': str(i)} for i in _xrange(50)]
        with self.dynamo.batch_write('foobar') as batch:
            for key in keys:
                batch.put(key)
        ret = list(self.dynamo.batch_get('foobar', keys))
        self.assertItemsEqual(ret, keys)

    def test_attributes(self):
        """ Can limit fetch to specific attributes """
        self.make_table()
        self.dynamo.put_item('foobar', {'id': 'a', 'foo': 'bar'})
        ret = list(self.dynamo.batch_get('foobar', [{'id': 'a'}],
                                         attributes=['id']))
        self.assertItemsEqual(ret, [{'id': 'a'}])

    def test_handle_unprocessed(self):
        """ Batch get retries unprocessed keys """
        conn = MagicMock()
        # Pass responses through dynamizer unchanged
        conn.dynamizer.decode_keys.side_effect = lambda x: x
        key1, key2 = object(), object()
        unprocessed = [[key1], [key2], []]
        conn.call.side_effect = lambda *_, **__: {
            'UnprocessedKeys': {
                'foo': {
                    'Keys': unprocessed[0],
                },
            },
            'Responses': {
                'foo': unprocessed.pop(0),
            },
        }
        rs = GetResultSet(conn, 'foo', [{'id': 'a'}])
        results = list(rs)
        self.assertEqual(results, [key1, key2])

    def test_capacity(self):
        """ Can return consumed capacity """
        conn = MagicMock()
        conn.call.return_value = {
            'Responses': {
                'foo': [],
            },
            'ConsumedCapacity': {
                'CapacityUnits': 3,
                'Table': {
                    'CapacityUnits': 1,
                },
                'LocalSecondaryIndexes': {
                    'l-index': {
                        'CapacityUnits': 1,
                    },
                },
                'GlobalSecondaryIndexes': {
                    'g-index': {
                        'CapacityUnits': 1,
                    },
                },
            },
        }
        rs = GetResultSet(conn, 'foo', [{'id': 'a'}])
        list(rs)
        self.assertEqual(rs.capacity, 3)
        self.assertEqual(rs.table_capacity, 1)
        self.assertEqual(rs.indexes, {'l-index': 1})
        self.assertEqual(rs.global_indexes, {'g-index': 1})


class TestGetItem(BaseSystemTest):

    """ Tests for the GetItem call """

    def make_table(self):
        """ Convenience method for making a table """
        hash_key = DynamoKey('id')
        self.dynamo.create_table('foobar', hash_key=hash_key)

    def test_get(self):
        """ Can fetch an item by the primary key """
        self.make_table()
        item = {'id': 'a', 'foo': 'bar'}
        self.dynamo.put_item('foobar', item)
        ret = self.dynamo.get_item('foobar', {'id': 'a'})
        self.assertEqual(ret, item)

    def test_attribute(self):
        """ Can fetch only certain attributes """
        self.make_table()
        item = {'id': 'a', 'foo': 'bar'}
        self.dynamo.put_item('foobar', item)
        ret = self.dynamo.get_item('foobar', {'id': 'a'}, attributes=['id'])
        self.assertEqual(ret, {'id': 'a'})

    def test_capacity(self):
        """ Can return the consumed capacity as well """
        self.make_table()
        self.dynamo.put_item('foobar', {'id': 'a'})
        ret = self.dynamo.get_item('foobar', {'id': 'a'},
                                   return_capacity=TOTAL)
        self.assertTrue(is_number(ret.capacity))
        self.assertTrue(is_number(ret.table_capacity))
        self.assertTrue(isinstance(ret.indexes, dict))
        self.assertTrue(isinstance(ret.global_indexes, dict))

    def test_result_repr(self):
        """ Result repr should not be the same as a dict """
        d = {'a': 'b'}
        response = {'Item': self.dynamo.dynamizer.encode_keys(d)}
        result = Result(self.dynamo.dynamizer, response, 'Item')
        self.assertNotEqual(repr(result), repr(d))
