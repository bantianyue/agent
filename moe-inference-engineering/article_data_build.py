# -*- coding: utf-8 -*-
import json, os, sys
_d = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else '.')
DATA = json.load(open(os.path.join(_d, '_data.json'), encoding='utf-8'))
