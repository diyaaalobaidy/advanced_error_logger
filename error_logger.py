from datetime import datetime
import os
from uuid import uuid4
from sqlalchemy import create_engine,Column,String,Integer,DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
import traceback
import sys

def generate_uuid():
    return str(uuid4())

db=create_engine("sqlite:///errors.db")
session=sessionmaker()
session.configure(bind=db)
session=session()
Base=declarative_base(db.engine)
class Error(Base):
    __tablename__="error_log"
    identifier=Column(String(),default=generate_uuid,primary_key=True,comment="A unique ID for the error")
    error_file=Column(String(),nullable=False,comment="File at which the error occurred")
    error_lnno=Column(Integer,nullable=False,comment="Line number where the error occurred")
    error_text=Column(String(),nullable=False,comment="The message of the error")
    error_func=Column(String(),nullable=False,comment="The function at which the error occurred")
    error_type=Column(String(),nullable=False,comment="The type of the error")
    error_tbck=Column(String(),nullable=False,comment="File name where the full traceback of the error is stored")
    created_at=Column(DateTime(),nullable=False,default=datetime.now,comment="Time at which the error occurred")

    def save(self):
        try:
            session.add(self)
            session.commit()
        except Exception as e:
            self.unhandled_exception(e)

    def get(self):
        try:
            return{
                "identifier": self.identifier,
                "error_file": self.error_file,
                "error_lnno": self.error_lnno,
                "error_text": self.error_text,
                "error_func": self.error_func,
                "error_tbck": self.error_tbck,
                "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            }
        except Exception as e:
            self.unhandled_exception(e)

    def unhandled_exception(self,e: Exception):
        with open("unhandled_errors.log","a+",encoding="utf8") as f:
            f.write("\n{}\n".format("|"*120))
            f.write("{}{}".format(" "*50,datetime.now()))
            f.write("\n{}\n".format("|"*120))
            f.write(traceback.format_exc())
        session.rollback()

Base.metadata.create_all()

def log_error(error:Exception,log_dir="logs")->str:
    """
    Logs errors to sqlite3 database file
    """
    exc_type, exc_value, exc_traceback = sys.exc_info()
    filename=exc_traceback.tb_frame.f_code.co_filename
    lineno= exc_traceback.tb_lineno
    name= exc_traceback.tb_frame.f_code.co_name
    err_type= exc_type.__name__
    message=exc_value.args[0]
    os.makedirs(log_dir,exist_ok=True)
    log_file_name="{}/{}-{}.log".format(log_dir,datetime.now().strftime("%Y%m%d%H%M%S"),generate_uuid())
    with open(log_file_name,"w",encoding="utf8") as f:
            f.write("\n{}\n".format("|"*120))
            f.write("{}{}".format(" "*50,datetime.now()))
            f.write("\n{}\n".format("|"*120))
            f.write(traceback.format_exc())
    log=Error(error_file=filename,error_lnno=lineno,error_func=name,error_text=message,error_type=err_type,error_tbck=log_file_name)
    log.save()
    return log.get()

def track_error(log_dir="logs"):
    def wrapper(function):
        def func(*args,**kwargs):
            try:
                return function(*args,**kwargs)
            except Exception as e:
                return log_error(e, log_dir=log_dir)
        func.__name__=function.__name__+"_wrapper"
        return func
    return wrapper

# Example:
# @track_error("my_custom_log_folder")
# def errored(a,b):
#     print(a/b)

# if __name__=="__main__":
#     print(errored(1,0))