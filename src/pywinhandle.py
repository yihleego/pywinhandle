from ctypes import *
from ctypes.wintypes import *

from win32api import *
from win32process import *

ntdll = WinDLL('ntdll')
current_process = GetCurrentProcess()

NTSTATUS = LONG
ULONG_PTR = WPARAM
ACCESS_MASK = DWORD

STATUS_SUCCESS = NTSTATUS(0).value
STATUS_BUFFER_OVERFLOW = NTSTATUS(0x80000005).value
STATUS_NO_MORE_FILES = NTSTATUS(0x80000006).value
STATUS_INFO_LENGTH_MISMATCH = NTSTATUS(0xC0000004).value

DUPLICATE_CLOSE_SOURCE = 0x00000001
DUPLICATE_SAME_ACCESS = 0x00000002
DUPLICATE_SAME_ATTRIBUTES = 0x00000004

STANDARD_RIGHTS_REQUIRED = 0x000F0000
SYNCHRONIZE = 0x00100000
PROCESS_TERMINATE = 0x0001
PROCESS_CREATE_THREAD = 0x0002
PROCESS_SET_SESSIONID = 0x0004
PROCESS_VM_OPERATION = 0x0008
PROCESS_VM_READ = 0x0010
PROCESS_VM_WRITE = 0x0020
PROCESS_DUP_HANDLE = 0x0040
PROCESS_CREATE_PROCESS = 0x0080
PROCESS_SET_QUOTA = 0x0100
PROCESS_SET_INFORMATION = 0x0200
PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_SUSPEND_RESUME = 0x0800
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
PROCESS_ALL_ACCESS = (STANDARD_RIGHTS_REQUIRED | SYNCHRONIZE | 0xfff)

SYSTEM_INFORMATION_CLASS = ULONG
SystemExtendedHandleInformation = ULONG(64)

OBJECT_INFORMATION_CLASS = ULONG
ObjectBasicInformation = ULONG(0)
ObjectNameInformation = ULONG(1)
ObjectTypeInformation = ULONG(2)

ntdll.NtQuerySystemInformation.restype = NTSTATUS
ntdll.NtQuerySystemInformation.argtypes = [
    SYSTEM_INFORMATION_CLASS,
    LPVOID,
    ULONG,
    PULONG]

ntdll.NtQueryObject.restype = NTSTATUS
ntdll.NtQueryObject.argtypes = [
    HANDLE,
    OBJECT_INFORMATION_CLASS,
    LPVOID,
    ULONG,
    PULONG]

ntdll.NtDuplicateObject.restype = NTSTATUS
ntdll.NtDuplicateObject.argtypes = [
    HANDLE,
    HANDLE,
    HANDLE,
    PHANDLE,
    ACCESS_MASK,
    ULONG,
    ULONG]


class UNICODE_STRING(Structure):
    _fields_ = [
        ('Length', USHORT),
        ('MaximumLength', USHORT),
        ('Buffer', LPWSTR * 4096),
    ]


class SYSTEM_HANDLE(Structure):
    _fields_ = [
        ('Object', LPVOID),
        ('UniqueProcessId', HANDLE),
        ('HandleValue', HANDLE),
        ('GrantedAccess', ULONG),
        ('CreatorBackTraceIndex', USHORT),
        ('ObjectTypeIndex', USHORT),
        ('HandleAttributes', ULONG),
        ('Reserved', ULONG),
    ]


class SYSTEM_HANDLE_INFORMATION_EX(Structure):
    _fields_ = [
        ('HandleCount', ULONG_PTR),
        ('Reserved', ULONG_PTR),
        ('Handles', SYSTEM_HANDLE * 2),
    ]


class OBJECT_BASIC_INFORMATION(Structure):
    _fields_ = [
        ('Attributes', ULONG),
        ('GrantedAccess', ACCESS_MASK),
        ('HandleCount', ULONG),
        ('PointerCount', ULONG),
        ('PagedPoolCharge', ULONG),
        ('NonPagedPoolCharge', ULONG),
        ('Reserved', ULONG * 3),
        ('NameInfoSize', ULONG),
        ('TypeInfoSize', ULONG),
        ('SecurityDescriptorSize', ULONG),
        ('CreationTime', LARGE_INTEGER),
    ]


class OBJECT_NAME_INFORMATION(Structure):
    _fields_ = [
        ('Name', UNICODE_STRING),
    ]


class OBJECT_TYPE_INFORMATION(Structure):
    _fields_ = [
        ('TypeName', UNICODE_STRING),
        ('Reserved', ULONG * 22),
    ]


def query_handle_info():
    current_length = 0x10000
    while True:
        if current_length > 0x4000000:
            return

        class SYSTEM_HANDLE_INFORMATION_EX(Structure):
            _fields_ = [
                ('HandleCount', ULONG_PTR),
                ('Reserved', ULONG_PTR),
                ('Handles', SYSTEM_HANDLE * current_length)
            ]

        buf = SYSTEM_HANDLE_INFORMATION_EX()
        return_length = c_ulong(current_length)
        status = ntdll.NtQuerySystemInformation(SystemExtendedHandleInformation, byref(buf), return_length, byref(return_length))
        if status == STATUS_SUCCESS:
            return buf
        elif status == STATUS_INFO_LENGTH_MISMATCH:
            current_length *= 8
            continue
        else:
            return None


def duplicate_object(source_process_handle, source_handle):
    h = HANDLE()
    status = ntdll.NtDuplicateObject(source_process_handle, source_handle, current_process, byref(h), 0, 0, DUPLICATE_SAME_ACCESS | DUPLICATE_SAME_ATTRIBUTES)
    if status == STATUS_SUCCESS:
        return h
    else:
        return None


def query_object_basic_info(h):
    basic_info = OBJECT_BASIC_INFORMATION()
    return_length = c_ulong(sizeof(OBJECT_BASIC_INFORMATION))
    status = ntdll.NtQueryObject(h, ObjectBasicInformation, byref(basic_info), return_length, byref(return_length))
    if status == STATUS_SUCCESS:
        return basic_info
    elif status == STATUS_INFO_LENGTH_MISMATCH:
        return None
    else:
        return None


def query_object_name_info(h, length):
    name_info = OBJECT_NAME_INFORMATION()
    return_length = c_ulong(length + sizeof(OBJECT_NAME_INFORMATION))
    status = ntdll.NtQueryObject(h, ObjectNameInformation, byref(name_info), return_length, byref(return_length))
    if status == STATUS_SUCCESS:
        return name_info
    elif status == STATUS_INFO_LENGTH_MISMATCH:
        return None
    else:
        return None


def query_object_type_info(h, length):
    type_info = OBJECT_TYPE_INFORMATION()
    return_length = c_ulong(length + sizeof(OBJECT_TYPE_INFORMATION))
    status = ntdll.NtQueryObject(h, ObjectTypeInformation, byref(type_info), return_length, byref(return_length))
    if status == STATUS_SUCCESS:
        return type_info
    elif status == STATUS_INFO_LENGTH_MISMATCH:
        return None
    else:
        return None


def find_handles(pids=None, names=None, close=False):
    res = []
    handle_info = query_handle_info()
    handle_list = handle_info.Handles[:handle_info.HandleCount]
    for handle in handle_list:
        handle_value = handle.HandleValue
        unique_process_id = handle.UniqueProcessId
        handle_name = None
        handle_type = None
        if pids and unique_process_id not in pids:
            continue
        try:
            source_process = OpenProcess(PROCESS_ALL_ACCESS | PROCESS_DUP_HANDLE | PROCESS_SUSPEND_RESUME, False, unique_process_id)
        except:
            continue
        duplicated_handle = duplicate_object(source_process.handle, handle_value)
        if duplicated_handle:
            basic_info = query_object_basic_info(duplicated_handle)
            if basic_info:
                handle_name_size = basic_info.NameInfoSize
                handle_type_size = basic_info.TypeInfoSize
                if handle_name_size > 0:
                    name_info = query_object_name_info(duplicated_handle, handle_name_size)
                    if name_info:
                        handle_name = name_info.Name.Buffer[0]
                if handle_type_size > 0:
                    type_info = query_object_type_info(duplicated_handle, handle_type_size)
                    if type_info:
                        handle_type = type_info.TypeName.Buffer[0]
        if names:
            if not handle_name:
                continue
            matched = False
            for n in names:
                if n in handle_name:
                    matched = True
                    break
            if not matched:
                continue
            if close:
                h_process = OpenProcess(PROCESS_DUP_HANDLE, False, unique_process_id)
                DuplicateHandle(h_process, handle_value, 0, 0, 0, DUPLICATE_CLOSE_SOURCE)
                CloseHandle(h_process)
        res.append({'pid': unique_process_id,
                    'handle': handle_value,
                    'name': handle_name,
                    'type': handle_type})
    return res