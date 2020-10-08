"""This module contains `JSONObject`, the main base class of JSON Classes.
"""
from __future__ import annotations
from typing import Dict, Any, Optional, ClassVar, TypeVar
from dataclasses import dataclass, fields as dataclass_fields
from .config import Config
from .exceptions import ValidationException
from .fields import FieldStorage, FieldType, other_field, fields
from .validators.instanceof_validator import InstanceOfValidator
from .contexts import TransformingContext, ValidatingContext, ToJSONContext
from .lookup_map import LookupMap
from .owned_dict import OwnedDict
from .owned_list import OwnedList


@dataclass(init=False)
class JSONObject:
    """JSONObject is the base class of JSON Classes objects. It provides
    crutial instance methods e.g. __init__, set, update, validate and tojson.

    To declare a new JSON Class, use the following syntax:

      from jsonclasses import jsonclass, JSONObject, types

      @jsonclass
      class MyObject(JSONObject):
        my_field_one: str = types.str.required
        my_field_two: int = types.int.range(0, 10).required
    """

    config: ClassVar[Config]

    def __init__(self: T, **kwargs: Any) -> None:
        """Initialize a new jsonclass object from keyed arguments or a dict.
        This method is suitable for accepting web and malformed inputs. Eager
        validation and transformation are applied during the initialization
        process.
        """
        for field in dataclass_fields(self):
            setattr(self, field.name, None)
        self.__set(fill_blanks=True, **kwargs)

    def set(self: T, **kwargs: Any) -> T:
        """Set object values in a batch. This method is suitable for web and
        fraud inputs. This method takes accessor marks into consideration,
        means readonly and internal field values will be just ignored.
        Writeonce fields are accepted only if the current value is None. This
        method triggers eager validation and transform. This method returns
        self, thus you can chain calling with other instance methods.
        """
        self.__set(fill_blanks=False, **kwargs)
        return self

    def __set(self: T, fill_blanks: bool = False, **kwargs: Any) -> None:
        """Set values of a JSON Class object internally."""
        validator = InstanceOfValidator(self.__class__)
        config = self.__class__.config
        context = TransformingContext(
            value=kwargs,
            keypath_root='',
            root=self,
            config_root=config,
            keypath_owner='',
            owner=self,
            config_owner=config,
            keypath_parent='',
            parent=self,
            field_description=None,
            all_fields=True,
            dest=self,
            fill_dest_blanks=fill_blanks,
            lookup_map=LookupMap())
        validator.transform(context)

    def update(self: T, **kwargs: Any) -> T:
        """Update object values in a batch. This method is suitable for
        internal inputs. This method ignores accessor marks, thus you can
        update readonly and internal values through this method. Writeonce
        doesn't have effect on this method. You can change writeonce fields'
        value freely in this method. This method does not trigger eager
        validation and transform. You should pass valid and final form values
        through this method. This method returns self, thus you can chain
        calling with other instance methods.
        """
        unallowed_keys = set(kwargs.keys()) - set(self.__dict__.keys())
        unallowed_keys_length = len(unallowed_keys)
        if unallowed_keys_length > 0:
            keys_list = ', '.join(list(unallowed_keys))
            raise ValueError(f'`{keys_list}` not allowed in '
                             f'{self.__class__.__name__}.')
        for key, item in kwargs.items():
            setattr(self, key, item)
        return self

    def tojson(self: T, ignore_writeonly: bool = False) -> Dict[str, Any]:
        """Serialize this JSON Class object to JSON dict.

        Args:
          ignore_writeonly (Optional[bool]): Whether ignore writeonly marks on
          fields. Be careful when setting it to True.

        Returns:
          dict: A dict represents this object's JSON object.
        """
        validator = InstanceOfValidator(self.__class__)
        config = self.__class__.config
        context = ToJSONContext(value=self,
                                config=config,
                                ignore_writeonly=ignore_writeonly)
        return validator.tojson(context)

    def validate(self: T, all_fields: Optional[bool] = None) -> T:
        """Validate the jsonclass object's validity. Raises ValidationException
        on validation failed.

        Args:
          all_fields (bool): Whether continue validation to fetch more error
          messages after the first error is found. This is useful when you are
          building a frontend form and want to display detailed messages.

        Returns:
          None: upon successful validation, returns nothing.
        """
        config = self.__class__.config
        context = ValidatingContext(
            value=self,
            keypath_root='',
            root=self,
            config_root=config,
            keypath_owner='',
            owner=self,
            config_owner=config,
            keypath_parent='',
            parent=self,
            field_description=None,
            all_fields=all_fields,
            lookup_map=LookupMap())
        InstanceOfValidator(self.__class__).validate(context)
        return self

    def is_valid(self: T) -> bool:
        """Test whether the jsonclass object is valid or not. This method
        triggers object validation.

        Returns:
          bool: the validity of the object.
        """
        try:
            self.validate(all_fields=False)
        except ValidationException:
            return False
        return True

    def __setattr__(self: T, name: str, value: Any) -> None:
        if isinstance(value, list):
            owned_list = OwnedList[Any](value)
            owned_list.owner = self
            owned_list.keypath = name
            super().__setattr__(name, owned_list)
        elif isinstance(value, dict):
            owned_dict = OwnedDict[str, Any](value)
            owned_dict.owner = self
            owned_dict.keypath = name
            super().__setattr__(name, owned_dict)
        else:
            super().__setattr__(name, value)
            if not isinstance(value, JSONObject):
                return
            sfield = next(f for f in fields(self) if f.field_name == name)
            fdesc = sfield.field_description
            fstore = fdesc.field_storage
            if fstore == FieldStorage.LOCAL_KEY or fstore == FieldStorage.FOREIGN_KEY:
                ofield = other_field(self, value, sfield)
                if ofield is not None:
                    if ofield.field_description.field_type == FieldType.INSTANCE:
                        if getattr(value, ofield.field_name) != self:
                            setattr(value, ofield.field_name, self)
                    elif ofield.field_description.field_type == FieldType.LIST:
                        if not isinstance(getattr(value, ofield.field_name),
                                          list):
                            setattr(value, ofield.field_name, [self])
                        else:
                            if self not in getattr(value, ofield.field_name):
                                getattr(value, ofield.field_name).append(self)


    def __odict_add__(self, odict: OwnedDict, key: str, val: Any) -> None:
        pass

    def __odict_del__(self, odict: OwnedDict, val: Any) -> None:
        pass

    def __olist_add__(self, olist: OwnedList, idx: int, val: Any) -> None:
        pass

    def __olist_del__(self, olist: OwnedList, val: Any) -> None:
        pass

    def __olist_sor__(self, olist: OwnedList) -> None:
        pass


T = TypeVar('T', bound=JSONObject)
