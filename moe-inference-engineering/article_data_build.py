# -*- coding: utf-8 -*-
import json, os
_p = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_data.json')
DATA = json.load(open(_p, encoding='utf-8'))
