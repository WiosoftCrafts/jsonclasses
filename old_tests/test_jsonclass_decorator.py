from __future__ import annotations
from unittest import TestCase
from jsonclasses import jsonclass, JSONObject
from jsonclasses.class_graph import class_graph_map, JSONClassRedefinitionError
from jsonclasses.config import Config


class TestJsonClassDecorator(TestCase):

    def test_json_class_decorator_works_alone(self):
        @jsonclass
        class MyJSONClassDecoratorTestObject(JSONObject):
            str_field: str
            int_field: str
        self.assertTrue(issubclass(MyJSONClassDecoratorTestObject, JSONObject))

    def test_json_class_decorator_works_with_graph(self):
        @jsonclass(class_graph='my-secret-graph-087')
        class MyJSONClassDecoratorTestObjectInMyGraph(JSONObject):
            str_field: str
            int_field: str
        self.assertTrue(issubclass(MyJSONClassDecoratorTestObjectInMyGraph, JSONObject))

    def test_json_class_decorator_without_args_raises_value_error_if_decorated_is_not_class(self):
        with self.assertRaisesRegex(ValueError, '@jsonclass should be used to decorate a class\\.'):
            @jsonclass
            def _my_method():
                pass

    def test_json_class_decorator_with_args_raises_value_error_if_decorated_is_not_class(self):
        with self.assertRaisesRegex(ValueError, '@jsonclass should be used to decorate a class\\.'):
            @jsonclass(class_graph='my-secret-graph-087')
            def _my_method():
                pass

    def test_json_class_decorator_without_args_raises_value_error_if_decorated_is_not_subclass_of_json_object(self):
        with self.assertRaisesRegex(ValueError, '@jsonclass should be used to decorate subclasses of JSONObject\\.'):
            @jsonclass
            class _MyOwnClass():
                pass

    def test_json_class_decorator_with_args_raises_value_error_if_decorated_is_not_subclass_of_json_object(self):
        with self.assertRaisesRegex(ValueError, '@jsonclass should be used to decorate subclasses of JSONObject\\.'):
            @jsonclass(class_graph='my-secret-graph-087')
            class _MyOwnClass():
                pass

    def test_json_class_decorator_without_graph_registers_class_in_default_graph(self):
        @jsonclass
        class MyJSONClassDecoratorTestObjectInDefaultGraph(JSONObject):
            str_field: str
            int_field: str
        class_from_map = class_graph_map.graph('default').get('MyJSONClassDecoratorTestObjectInDefaultGraph')
        self.assertTrue(MyJSONClassDecoratorTestObjectInDefaultGraph is class_from_map)

    def test_json_class_decorator_with_graph_registers_class_in_designated_graph(self):
        @jsonclass(class_graph='my-secret-graph-087')
        class MyJSONClassDecoratorTestObjectInDefaultGraph(JSONObject):
            str_field: str
            int_field: str
        class_from_map = class_graph_map.graph('my-secret-graph-087').get('MyJSONClassDecoratorTestObjectInDefaultGraph')
        self.assertTrue(MyJSONClassDecoratorTestObjectInDefaultGraph is class_from_map)

    def test_json_class_decorator_installs_config_on_class(self):
        @jsonclass(class_graph='my-secret-graph-087')
        class MyClassThatHasConfig(JSONObject):
            str_field: str
            int_field: str
        config = MyClassThatHasConfig.config
        self.assertTrue(isinstance(config, Config))
        del config.linked_class
        self.assertEqual(config, Config(class_graph='my-secret-graph-087', camelize_json_keys=True, camelize_db_keys=True))

    def test_json_class_decorator_pass_settings_camelize_json_to_class(self):
        @jsonclass(class_graph='my-secret-graph-087', camelize_json_keys=False)
        class MyClassThatHasConfigWithJSONKey(JSONObject):
            str_field: str
            int_field: str
        config = MyClassThatHasConfigWithJSONKey.config
        self.assertTrue(isinstance(config, Config))
        del config.linked_class
        self.assertEqual(config, Config(class_graph='my-secret-graph-087', camelize_json_keys=False, camelize_db_keys=True))

    def test_json_class_decorator_pass_settings_camelize_db_to_class(self):
        @jsonclass(class_graph='my-secret-graph-087', camelize_db_keys=False)
        class MyClassThatHasConfigWithDBKey(JSONObject):
            str_field: str
            int_field: str
        config = MyClassThatHasConfigWithDBKey.config
        self.assertTrue(isinstance(config, Config))
        del config.linked_class
        self.assertEqual(config, Config(class_graph='my-secret-graph-087', camelize_json_keys=True, camelize_db_keys=False))

    def test_json_class_decorator_throws_if_defined_duplicate_name_class_on_same_graph(self):
        with self.assertRaisesRegex(JSONClassRedefinitionError, 'Cannot define new JSON Class with same name in same graph'):
            @jsonclass(class_graph='my-secret-graph-087', camelize_json_keys=False)
            class MyClassThatHasConfigWithJSONKey(JSONObject):
                str_field: str
                int_field: str
            MyClassThatHasConfigWithJSONKey()

    def test_json_class_decorator_get_config_linked_with_class(self):
        @jsonclass(class_graph='my-secret-graph-087', camelize_db_keys=False)
        class MyClassThatConfigLinks(JSONObject):
            str_field: str
            int_field: str
        config = MyClassThatConfigLinks.config
        self.assertTrue(isinstance(config, Config))
        self.assertIs(config.linked_class, MyClassThatConfigLinks)

    def test_jsonclass_decorator_call_loaded_callback_if_it_is_defined(self):
        value = {'a': 0}

        @jsonclass(class_graph='test_jsonclass_decorator_30')
        class ClassWithCallback(JSONObject):
            str_field: str
            int_field: int

            @classmethod
            def __loaded__(self: type[ClassWithCallback],
                           class_: type[ClassWithCallback]):
                value['a'] = 1
        self.assertEqual(value['a'], 1)