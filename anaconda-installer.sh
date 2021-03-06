#!/bin/bash

conda create -n psypy3 python=3.5
conda activate psypy3
conda install \
			numpy scipy matplotlib pandas pyopengl pillow \
			lxml openpyxl xlrd configobj pyyaml gevent greenlet \
			msgpack-python psutil pytables "requests[security]" \
			cffi seaborn wxpython cython pyzmq pyserial
conda install -c conda-forge pyglet pysoundfile python-bidi moviepy pyosf
pip install zmq json-tricks pyparallel sounddevice pygame pysoundcard psychopy_ext psychopy
