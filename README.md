# Pywinhandle

## Introduction

It is a utility that displays information about open handles for any process in the system. 
You can use it to see the programs that have a file open, 
or to see the object types and names of all the handles of a program, 
or to close the any handles of a program.

## Usage

### Find Handles

```python
handles = find_handles(process_ids=[0x6600], handle_names=['HandleName'])
```

Returns:

```python
[{'process_id': 0x6600, 'handle': 0x9900, 'name': 'HandleName', 'type': 'HandleType'}]
```

### Close Handle

```python
close_handle(process_id=0x6600, handle=0x9900)
```

## Links

### Win32 API

- [NtQuerySystemInformation function](https://docs.microsoft.com/en-us/windows/win32/api/winternl/nf-winternl-ntquerysysteminformation)
- [NtQueryObject function](https://docs.microsoft.com/en-us/windows/win32/api/winternl/nf-winternl-ntqueryobject)
- [ZwDuplicateObject function](https://docs.microsoft.com/en-us/windows-hardware/drivers/ddi/ntifs/nf-ntifs-zwduplicateobject)

### Process Utilities

- [Handle](https://docs.microsoft.com/en-us/sysinternals/downloads/handle)
- [Process Explorer](https://docs.microsoft.com/en-us/sysinternals/downloads/process-explorer)