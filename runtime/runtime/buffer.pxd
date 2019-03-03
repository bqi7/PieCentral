from libc.stdint cimport uint8_t
from libcpp.string cimport string
from posix.stat cimport mode_t
from posix.types cimport off_t


cdef extern from "<fcntl.h>":
    cpdef enum:
        O_CREAT
        O_EXCL
        O_NOCTTY
        O_TRUNC
        O_APPEND
        O_DSYNC
        O_NONBLOCK
        O_RSYNC
        O_SYNC
        O_ACCMODE
        O_RDONLY
        O_RDWR
        O_WRONLY


cdef extern from "<sys/stat.h>":
    cpdef enum:
        S_IRWXU
        S_IRUSR
        S_IWUSR
        S_IXUSR
        S_IRWXG
        S_IRGRP
        S_IWGRP
        S_IXGRP
        S_IRWXO
        S_IROTH
        S_IWOTH
        S_IXOTH
        S_ISUID
        S_ISGID
        S_ISVTX


cdef extern from "<sys/mman.h>":
    int shm_open(const char *, int, mode_t)
    int shm_unlink(const char *)
    void *mmap(void *, size_t, int, int, int, off_t)
    int munmap(void *, size_t)
    cpdef enum:
        PROT_READ
        PROT_WRITE
        PROT_EXEC
        PROT_NONE
        MAP_SHARED
        MAP_SHARED_VALIDATE
        MAP_PRIVATE
        MAP_32BIT
        MAP_ANONYMOUS
        MAP_DENYWRITE
        MAP_EXECUTABLE
        MAP_FILE
        MAP_FIXED
        MAP_FIXED_NOREPLACE
        MAP_GROWSDOWN
        MAP_HUGETLB
        MAP_LOCKED
        MAP_NONBLOCK
        MAP_NORESERVE
        MAP_POPULATE
        MAP_STACK
        MAP_SYNC


cdef extern from "ringbuffer.cpp":
    pass


cdef extern from "ringbuffer.cpp" namespace "ringbuffer":
    cdef cppclass RingBuffer:
        RingBuffer(size_t) nogil except +
        size_t size() nogil
        uint8_t operator[](size_t) nogil except +
        void extend(string) nogil except +
        string read() nogil except +