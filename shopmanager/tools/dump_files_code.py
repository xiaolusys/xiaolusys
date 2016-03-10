import os
import sys
import time

def dump_app_code_to_file(fp,sf):
    
    for f in os.listdir(fp):
        f = os.path.join(fp,f)
        if os.path.isdir(f):
            dump_app_code_to_file(f,sf)
        elif os.path.isfile(f) and f.endswith('.py'):
            with open(f,'r') as fs:
                lines = fs.readlines()
                for line in lines:
                    if not line.strip() or line.strip().startswith('#'):
                        continue
                    print >> sf, line.rstrip()
    

if __name__ == '__main__':
    
    if len(sys.argv) < 2:
        print "usage:python <exec-file.py> <filepath1> <filepath2> <...>"
        
    filepaths = sys.argv[1:]
    print 'debug:file paths = ',filepaths
    for fp in filepaths:
        if not os.path.exists(fp):
            print 'path:%s is not exists'%fp
    
    with open('/tmp/%d.py'%time.time(),'w+') as tmpf:
        for fp in filepaths:
            dump_app_code_to_file(fp,tmpf)
