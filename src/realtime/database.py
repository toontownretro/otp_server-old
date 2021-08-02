"""
 * Copyright (C) Caleb Marshall - All Rights Reserved
 * Written by Caleb Marshall <anythingtechpro@gmail.com>, August 17th, 2017
 * Licensing information can found in 'LICENSE', which is part of this source code package.
"""

import os
import collections
import threading

import simplejson
import yaml
import pytoml

from panda3d.core import *
from panda3d.direct import *

from direct.fsm.FSM import FSM

from otp_server.realtime import io
from otp_server.realtime import types
from otp_server.realtime.notifier import notify

class DatabaseError(RuntimeError):
    """
    An database specific runtime error
    """

class DatabaseFile(object):
    """
    An file object that represents a file in memory,
    containing all of the valid fields...
    """

    def __init__(self, database_manager):
        self._database_manager = database_manager
        self._filename = None
        self._data = {}
        self._mutex_lock = threading.RLock()

    @property
    def filename(self):
        return self._filename

    @filename.setter
    def filename(self, filename):
        if self._filename == filename:
            raise DatabaseError('Cannot set filename to of which did not change!')

        self._filename = filename

    @property
    def filepath(self):
        return self._database_manager.get_filepath(self._filename)

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, data):
        if not isinstance(data, dict):
            raise DatabaseError('Cannot set data property to of invalid type!')

        self._data = data

    def setup(self):
        """
        Initializes the file object and reads it's values from disk.
        """

        if os.path.exists(self.filepath):
            self.load()

    def has_value(self, key):
        """
        Returns true if the key is in the dictionary else false.
        """

        return key in self._data

    def set_value(self, key, value):
        """
        Sets the key assigned to the value in the dictionary.
        """

        self._data[key] = value
        self.save()

    def set_default_value(self, key, default_value):
        """
        Returns the value if the key exists in the dictionary else,
        returns the default_value and places the default_value in the dictionary
        assigned to as the specified key...
        """

        if self.has_value(key):
            return self.get_value(key)

        self.set_value(key, default_value)
        return default_value

    def get_value(self, key):
        """
        Gets the value from the key within the dictionary.
        """

        self.load()
        return self._data.get(key)

    def save(self):
        """
        Safely saves the file data to disk using a mutex lock,
        so the process is thread safe...
        """

        with self._mutex_lock:
            self.handle_save()

    def handle_save(self):
        """
        Dumps the file from memory out to disk safely.
        """

    def load(self):
        """
        Safely loads the file data from disk using a mutex lock,
        so the process is thread safe...
        """

        with self._mutex_lock:
            self.handle_load()

    def handle_load(self):
        """
        Loads the file data from disk to memory safely.
        """

    def close(self):
        """
        Closes the file instance and saves the data in memory safely,
        out to disk then clears the file instance references.
        """

        self.save()

        self._database_manager = None
        self._filename = None
        self._data = None
        self._mutex_lock = None

class DatabaseJSONFile(DatabaseFile):

    def handle_save(self):
        with open(self.filepath, 'w') as io:
            simplejson.dump(self._data, io, indent=2, sort_keys=True)
            io.close()

    def handle_load(self):
        with open(self.filepath, 'r') as io:
            self._data = simplejson.load(io)
            io.close()

class DatabaseYAMLFile(DatabaseFile):

    def handle_save(self):
        with open(self.filepath, 'w') as io:
            yaml.dump(self._data, io, default_flow_style=False)
            io.close()

    def handle_load(self):
        with open(self.filepath, 'r') as io:
            self._data = yaml.load(io)
            io.close()

class DatabaseTOMLFile(DatabaseFile):

    def handle_save(self):
        with open(self.filepath, 'w') as io:
            pytoml.dump(self._data, io)
            io.close()

    def handle_load(self):
        with open(self.filepath, 'r') as io:
            self._data = pytoml.load(io)
            io.close()

class DatabaseManager(object):
    """
    An class that manages database file reading/writing operations,
    creates/destroys file object instances...
    """

    def __init__(self, file_object_handler, directory, file_extension):
        self._file_object_handler = file_object_handler
        self._directory = directory
        self._file_extension = file_extension
        self._files = {}

    @property
    def file_object_handler(self):
        return self._file_object_handler

    @property
    def directory(self):
        return self._directory

    @property
    def file_extension(self):
        return self._file_extension

    @property
    def files(self):
        return self._files

    def get_filepath(self, filename):
        """
        Returns the filename joined with the root database file directory.
        """

        return '%s%s' % (os.path.join(self._directory, filename), self._file_extension)

    def has_file(self, filename):
        """
        Returns true if the filename is in the file dictionary else false.
        """

        return filename in self._files

    def add_file(self, filename, *args, **kwargs):
        """
        Creates a new file instance in memory and loads the corresponding
        file object from disk, placing the data in memory
        """

        if self.has_file(filename):
            raise DatabaseError('Cannot open file: %s, file already open!' % (
                filename))

        file_object = self._file_object_handler(self)
        file_object.filename = filename

        self._files[file_object.filename] = file_object
        file_object.setup()

        return file_object

    def remove_file(self, file_object):
        """
        Removes a file instance in memory and closes the file,
        saving the data from memory to disk
        """

        if not self.has_file(file_object.filename):
            raise DatabaseError('Cannot close file: %s, file was never opened!' % (
                filename))

        del self._files[file_object.filename]
        file_object.close()

        del file_object

    def get_file(self, filename):
        """
        Gets a file instance object from the file dictionary by name.
        """

        return self._files.get(filename)

    def setup(self):
        """
        Initializes the database manager and any other specific operations...
        """

        if not os.path.exists(self._directory):
            os.makedirs(self._directory)

    def shutdown(self):
        """
        Destroys all file object instances and saves them to disk.
        """

        for filename, file_object in self._files.items():
            self.remove_file(file_object)

class DatabaseInterface(DatabaseManager):

    def __init__(self, file_object):
        directory = config.GetString('database-directory', 'databases/json')
        extension = config.GetString('database-extension', '.json')

        DatabaseManager.__init__(self, file_object, directory, extension)

        self._min_id = config.GetInt('database-min-channels', 1000000000)
        self._max_id = config.GetInt('database-max-channels', 1009999999)

        self._tracker = None
        self._tracker_filename = config.GetString('database-tracker', 'next')

        self._allocator = None

    @property
    def tracker(self):
        return self._tracker

    @property
    def allocator(self):
        return self._allocator

    def setup(self):
        DatabaseManager.setup(self)

        self._tracker = self.add_file(self._tracker_filename)
        self._tracker.save()

        self._min_id = self._tracker.set_default_value('next', self._min_id)
        self._allocator = UniqueIdAllocator(self._min_id, self._max_id)

    def shutdown(self):
        self._tracker = None
        self._min_id = None
        self._max_id = None
        self._allocator = None

        DatabaseManager.shutdown(self)

class DatabaseJSONBackend(DatabaseInterface):

    def __init__(self):
        DatabaseInterface.__init__(self, DatabaseJSONFile)

class DatabaseYAMLBackend(DatabaseInterface):

    def __init__(self):
        DatabaseInterface.__init__(self, DatabaseYAMLFile)

class DatabaseTOMLBackend(DatabaseInterface):

    def __init__(self):
        DatabaseInterface.__init__(self, DatabaseTOMLFile)

class DatabaseOperationFSM(FSM):
    notify = notify.new_category('DatabaseOperationFSM')

    def __init__(self, network, sender):
        FSM.__init__(self, self.__class__.__name__)

        self._network = network
        self._sender = sender

    @property
    def network(self):
        return self._network

    @property
    def sender(self):
        return self._sender

    def enterStart(self):
        self.demand('Stop')

    def exitStart(self):
        pass

    def enterStop(self):
        self.demand('Off')

    def exitStop(self):
        self._network = None
        self._sender = None

class DatabaseOperationManager(object):
    notify = notify.new_category('DatabaseOperationManager')

    def __init__(self):
        self._operations = collections.deque()
        self.__update_task = None

    @property
    def operations(self):
        return self._operations

    def add_operation(self, fsm_class, *args, **kwargs):
        operation = fsm_class(*args, **kwargs)
        self._operations.append(operation)

    def setup(self):
        self.__update_task = task_mgr.add(self.__update, 'database-update')

    def __update(self, task):
        """
        Gets an database operation from the queue and processes it...
        """

        if not len(self._operations):
            return task.cont

        operation = self._operations.popleft()
        operation.request('Start')

        return task.cont

    def shutdown(self):
        if self.__update_task:
            task_mgr.remove(self.__update_task)

        self._operations = None
        self.__update_task = None

class DatabaseCreateFSM(DatabaseOperationFSM):
    notify = notify.new_category('DatabaseCreateFSM')

    def __init__(self, *args, **kwargs):
        self._context = kwargs.pop('context', 0)
        self._dc_id = kwargs.pop('dc_id', 0)
        self._field_count = kwargs.pop('field_count', 0)
        self._field_data = kwargs.pop('field_data', None)

        DatabaseOperationFSM.__init__(self, *args, **kwargs)

    def enterStart(self):
        dc_class = self.network.dc_loader.dclasses_by_number.get(self._dc_id)
        if not dc_class:
            self.notify.error('Failed to create object: %d context: %d, unknown dclass!' % (
                self._dc_id, self._context))

        self._do_id = self.network.backend.allocator.allocate()
        file_object = self.network.backend.add_file('%d' % self._do_id)
        file_object.save()

        file_object.set_value('dclass', dc_class.get_name())
        file_object.set_value('do_id', self._do_id)

        fields = {}
        field_packer = DCPacker()
        field_packer.set_unpack_data(self._field_data)

        for _ in range(self._field_count):
            field_id = field_packer.raw_unpack_uint16()
            field = dc_class.get_field_by_index(field_id)
            if not field:
                self.notify.error('Failed to unpack field: %d dclass: %s, invalid field!' % (
                    field_id, dc_class.get_name()))

            field_packer.begin_unpack(field)
            field_args = field.unpack_args(field_packer)
            field_packer.end_unpack()
            if not field_args:
                self.notify.error('Failed to unpack field args for field: %d dclass: %s, invalid result!' % (
                    field.get_name(), dc_class.get_name()))

            fields[field.get_name()] = field_args

        for field_index in range(dc_class.get_num_inherited_fields()):
            field_packer = DCPacker()
            field = dc_class.get_inherited_field(field_index)

            if not field or field.get_name() in fields:
                continue

            if not field.is_db() or not field.has_default_value():
                continue

            field_packer.set_unpack_data(field.get_default_value())
            field_packer.begin_unpack(field)
            field_args = field.unpack_args(field_packer)
            field_packer.end_unpack()
            if not field_args:
                self.notify.error('Failed to unpack field args for field: %d dclass: %s, invalid result!' % (
                    field.get_name(), dc_class.get_name()))

            fields[field.get_name()] = field_args

        file_object.set_value('fields', fields)

        self.network.backend.remove_file(file_object)
        self.network.backend.tracker.set_value('next', self._do_id + 1)
        DatabaseOperationFSM.enterStart(self)

    def exitStart(self):
        pass

    def enterStop(self):
        datagram = io.NetworkDatagram()
        datagram.add_header(self.sender, self.network.channel,
            types.DBSERVER_CREATE_OBJECT_RESP)

        datagram.add_uint32(self._context)
        datagram.add_uint32(self._do_id)

        self.network.handle_send_connection_datagram(datagram)
        DatabaseOperationFSM.enterStop(self)

    def exitStop(self):
        self._context = None
        self._dc_id = None
        self._field_count = None
        self._field_data = None
        self._do_id = None
        
class DatabaseGetValuesFSM(DatabaseOperationFSM):
    notify = notify.new_category('DatabaseGetValuesFSM')

    def __init__(self, *args, **kwargs):
        self._context = kwargs.pop('context', 0)
        self._do_id = kwargs.pop('do_id', 0)
        self._di = kwargs.pop('di', 0)
        self._ret_code = 0

        DatabaseOperationFSM.__init__(self, *args, **kwargs)

    def enterStart(self):
        field_names = []
        num_fields = self._di.get_uint16()
        for i in range(0, num_fields):
            field_names.append(self._di.get_string())
        
        file_object = self.network.backend.add_file('%d' % self._do_id)
        if not file_object:
            self.notify.warning('Failed to get fields for object: %d context: %d, unknown object!' % (do_id, self._context))
            self._ret_code = 1
            DatabaseOperationFSM.enterStart(self)
            return

        dc_name = file_object.get_value('dclass')
        self._dc_class = self.network.dc_loader.dclasses_by_name.get(dc_name)
        if not self._dc_class:
            self.notify.warning('Failed to query object: %d context: %d, unknown dclass: %s!' % (self._do_id, self._context, dc_name))
            self._ret_code = 2
            DatabaseOperationFSM.enterStart(self)
            return
            
        file_fields = file_object.get_value('fields')
        if not file_fields:
            self.notify.warning('Failed to query object: %d context %d, invalid fields!' % (self._do_id, self._context))
            self._ret_code = 3
            DatabaseOperationFSM.enterStart(self)
            return
            
        # Remove the file object. We no longer need it.
        self.network.backend.remove_file(file_object)

        # Grab all of our fields we're going to use,
        # We don't want to return any we don't need.
        self._fields = {}
        for i in range(0, num_fields):
            field_name = field_names[i]
            field_data = file_fields.get(field_name, None)
            if not field_data:
                self._fields[field_name] = None
                continue
            self._fields[field_name] = field_data
            
        DatabaseOperationFSM.enterStart(self)

    def exitStart(self):
        pass

    def enterStop(self):
        # If we failed. We handle a special failure response..
        if self._ret_code != 0:
            datagram = io.NetworkDatagram()
            datagram.add_header(self.sender, self.network.channel, types.DBSERVER_GET_STORED_VALUES_RESP)
            
            datagram.add_uint32(self._context) # context - Even if we failed. We want send back their context.
            datagram.add_uint32(self._do_id) # do_id - Even if we failed. We want to inform who we failed to get.
            datagram.add_uint16(0) # field_count - We have no fields because we failed to get our object.
            datagram.add_uint8(self._ret_code) # return_code - We failed so we don't return 0 (Success), but instead our failure code.
            self.network.handle_send_connection_datagram(datagram)
            
            DatabaseOperationFSM.enterStop(self)
            return
            
        # Otherwise, Let's do as we planned.
        
        datagram = io.NetworkDatagram()
        datagram.add_header(self.sender, self.network.channel, types.DBSERVER_GET_STORED_VALUES_RESP)

        datagram.add_uint32(self._context) # context - We want to send them back their context.
        datagram.add_uint32(self._do_id) # do_id - This is needed for verification.
        datagram.add_uint16(len(self._fields)) # field_count - They need to know how many fields we've sent.
        
        # First we're going to pack our fields names.
        for field_name in self._fields.keys():
             datagram.add_string(field_name)
            
        datagram.add_uint8(0) # return_code - This was a successful retrieval of fields. So we return 0 (Success)
        
        found_field_map = []
        
        # Now we're going to pack our field data.
        for field_name, field_args in self._fields.items():
            field = self._dc_class.get_field_by_name(field_name)
            if not field or not field_args:
                self.notify.warning('Failed to pack object field %s: doId %d dcclass %s context %d' % (field_name, self._do_id, self._dc_class.get_name(), self._context))
                datagram.add_string("")
                found_field_map.append(False)
                continue
                
            field_packer = DCPacker()
            field_packer.begin_pack(field)
            field.pack_args(field_packer, field_args)
            field_packer.end_pack()
            
            datagram.append_string(field_packer.get_string())
            found_field_map.append(True)
            
        # Finally we're going to add if we successfully got the field or not.
        for i in range(0, len(found_field_map)):
            datagram.add_uint8(found_field_map[i])

        self.network.handle_send_connection_datagram(datagram)
        DatabaseOperationFSM.enterStop(self)

    def exitStop(self):
        self._context = None
        self._do_id = None
        self._dc_class = None
        self._fields = None
        self._ret_code = None
        
class DatabaseSetValuesFSM(DatabaseOperationFSM):
    notify = notify.new_category('DatabaseSetValuesFSM')

    def __init__(self, *args, **kwargs):
        self._do_id = kwargs.pop('do_id', 0)
        self._di = kwargs.pop('di', None)

        DatabaseOperationFSM.__init__(self, *args, **kwargs)

    def enterStart(self):
        file_object = self.network.backend.add_file('%d' % self._do_id)
        if not file_object:
            self.notify.warning('Failed to set fields for object: %d, unknown object!' % (self._do_id))
            return

        dc_name = file_object.get_value('dclass')
        dc_class = self.network.dc_loader.dclasses_by_name.get(dc_name)
        if not dc_class:
            self.notify.warning('Failed to set fields for object: %d, unknown dclass: %s!' % (self._do_id, dc_name))
            return

        fields = file_object.get_value('fields')
        if not fields:
            self.notify.warning('Failed to set fields for object: %d, invalid fields!' % (self._do_id))
            return
            
        # First we want to get all of our field names.
        field_names = []
        num_fields = self._di.get_uint16()
        for i in range(0, num_fields):
            field_names.append(self._di.get_string())
        
        # Now we want to unpack the stored data for our fields.
        # This should work fine because the names and corresponding
        # values are stored in the same order.
        for i in range(0, num_fields):
            field_name = field_names[i]
            field_packer = DCPacker()
            field_packer.set_unpack_data(self._di.get_string())
            
            field = dc_class.get_field_by_name(field_name)
            if not field:
                self.notify.warning('Failed to unpack field: %s dclass: %s, invalid field!' % (field_name, dc_class.get_name()))
                continue

            field_packer.begin_unpack(field)
            field_args = field.unpack_args(field_packer)
            field_packer.end_unpack()
            if not field_args:
                self.notify.warning('Failed to unpack field args for field: %s dclass: %s, invalid result!' % (field_name, dc_class.get_name()))
                continue

            fields[field.get_name()] = field_args
        
        # Now we'll update our file object with our new values.
        file_object.set_value('fields', fields)

        self.network.backend.remove_file(file_object)
        DatabaseOperationFSM.enterStart(self)

    def exitStart(self):
        pass

    def enterStop(self):
        DatabaseOperationFSM.enterStop(self)

    def exitStop(self):
        self._do_id = None
        self._di = None
        
class DatabaseRetrieveDepercatedFSM(DatabaseOperationFSM):
    notify = notify.new_category('DatabaseRetrieveDepercatedFSM')

    def __init__(self, *args, **kwargs):
        self._context = kwargs.pop('context', 0)
        self._do_id = kwargs.pop('do_id', 0)

        DatabaseOperationFSM.__init__(self, *args, **kwargs)

    def enterStart(self):
        file_object = self.network.backend.add_file('%d' % self._do_id)
        if not file_object:
            self.notify.warning('Failed to get fields for object: %d context: %d, unknown object!' % (do_id, self._context))
            return

        dc_name = file_object.get_value('dclass')
        self._dc_class = self.network.dc_loader.dclasses_by_name.get(dc_name)
        if not self._dc_class:
            self.notify.warning('Failed to query object: %d context: %d, unknown dclass: %s!' % (self._do_id, self._context, dc_name))
            return

        self._fields = file_object.get_value('fields')
        if not self._fields:
            self.notify.warning('Failed to query object: %d context %d, invalid fields!' % (self._do_id, self._context))
            return

        self.network.backend.remove_file(file_object)
        DatabaseOperationFSM.enterStart(self)

    def exitStart(self):
        pass

    def enterStop(self):
        field_packer = DCPacker()
        for field_name, field_args in self._fields.items():
            field = self._dc_class.get_field_by_name(field_name)
            if not field:
                self.notify.warning('Failed to query object %d context: %d, unknown field: %s' % (do_id, self._context, field_name))
                return

            field_packer.raw_pack_uint16(field.get_number())
            field_packer.begin_pack(field)
            field.pack_args(field_packer, field_args)
            field_packer.end_pack()

        datagram = io.NetworkDatagram()
        datagram.add_header(self.sender, self.network.channel, types.DBSERVER_OBJECT_GET_ALL_RESP)

        datagram.add_uint32(self._context)
        datagram.add_uint8(1)
        datagram.add_uint16(self._dc_class.get_number())
        datagram.add_uint16(len(self._fields))

        datagram.append_data(field_packer.get_string())
        self.network.handle_send_connection_datagram(datagram)
        DatabaseOperationFSM.enterStop(self)

    def exitStop(self):
        self._context = None
        self._do_id = None
        self._dc_class = None
        self._fields = None
        
class DatabaseSetFieldDepercatedFSM(DatabaseOperationFSM):
    notify = notify.new_category('DatabaseSetFieldDepercatedFSM')

    def __init__(self, *args, **kwargs):
        self._do_id = kwargs.pop('do_id', 0)
        self._field_data = kwargs.pop('field_data', None)

        DatabaseOperationFSM.__init__(self, *args, **kwargs)

    def enterStart(self):
        file_object = self.network.backend.add_file('%d' % self._do_id)
        if not file_object:
            self.notify.warning('Failed to set fields for object: %d, unknown object!' % (self._do_id))
            return

        dc_name = file_object.get_value('dclass')
        dc_class = self.network.dc_loader.dclasses_by_name.get(dc_name)
        if not dc_class:
            self.notify.warning('Failed to set fields for object: %d, unknown dclass: %s!' % (self._do_id, dc_name))
            return

        fields = file_object.get_value('fields')
        if not fields:
            self.notify.warning('Failed to set fields for object: %d, invalid fields!' % (self._do_id))
            return

        field_packer = DCPacker()
        field_packer.set_unpack_data(self._field_data)
        field_id = field_packer.raw_unpack_uint16()
        field = dc_class.get_field_by_index(field_id)
        if not field:
            self.notify.error('Failed to unpack field: %d dclass: %s, invalid field!' % (field_id, dc_class.get_name()))

        field_packer.begin_unpack(field)
        field_args = field.unpack_args(field_packer)
        field_packer.end_unpack()
        if not field_args:
            self.notify.error('Failed to unpack field args for field: %d dclass: %s, invalid result!' % (field.get_name(), dc_class.get_name()))

        fields[field.get_name()] = field_args
        file_object.set_value('fields', fields)

        self.network.backend.remove_file(file_object)
        DatabaseOperationFSM.enterStart(self)

    def exitStart(self):
        pass

    def enterStop(self):
        DatabaseOperationFSM.enterStop(self)

    def exitStop(self):
        self._do_id = None
        self._field_data = None

class DatabaseServer(io.NetworkConnector):
    notify = notify.new_category('DatabaseServer')

    def __init__(self, *args, **kwargs):
        io.NetworkConnector.__init__(self, *args, **kwargs)

        self._backend = DatabaseJSONBackend()
        self._operation_manager = DatabaseOperationManager()

    @property
    def backend(self):
        return self._backend

    @property
    def operation_manager(self):
        return self._operation_manager

    def setup(self):
        self._backend.setup()
        self._operation_manager.setup()

        io.NetworkConnector.setup(self)

    def handle_datagram(self, channel, sender, message_type, di):
        if message_type == types.DBSERVER_GET_STORED_VALUES:
            self.handle_object_get_values(sender, di)
        elif message_type == types.DBSERVER_SET_STORED_VALUES:
            self.handle_object_set_values(sender, di)
        # Handles for custom database types.
        elif message_type == types.DBSERVER_CREATE_OBJECT:
            self.handle_create_object(sender, di)
        elif message_type == types.DBSERVER_OBJECT_GET_ALL:
            self.handle_object_get_all(sender, di)
        elif message_type == types.DBSERVER_OBJECT_SET_FIELD:
            self.handle_object_set_field(sender, di)
        else:
            self.notify.warning('Received unknown message type: %d from sender %d!' % (message_type, sender))
            return
            
    # Handling functions for database types.
    
    def handle_object_get_values(self, sender, di):
        self._operation_manager.add_operation(DatabaseGetValuesFSM, self, sender,
            context=di.get_uint32(), do_id=di.get_uint32(), di=di)
            
    def handle_object_set_values(self, sender, di):
        self._operation_manager.add_operation(DatabaseSetValuesFSM, self, sender,
            do_id=di.get_uint32(), di=di)
            
    # Handling functions for custom database types.

    def handle_create_object(self, sender, di):
        self._operation_manager.add_operation(DatabaseCreateFSM, self, sender,
            context=di.get_uint32(), dc_id=di.get_uint16(), field_count=di.get_uint16(),
            field_data=di.get_remaining_bytes())

    def handle_object_get_all(self, sender, di):
        self._operation_manager.add_operation(DatabaseRetrieveDepercatedFSM, self, sender,
            context=di.get_uint32(), do_id=di.get_uint32())

    def handle_object_set_field(self, sender, di):
        self._operation_manager.add_operation(DatabaseSetFieldDepercatedFSM, self, sender,
            do_id=di.get_uint32(), field_data=di.get_remaining_bytes())

    def shutdown(self):
        self._backend.shutdown()
        self._operation_manager.shutdown()

        io.NetworkConnector.shutdown(self)
