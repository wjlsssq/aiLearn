"""清理过期 Excel 文件；可由运维计划任务调用，不删除聊天历史。"""

from time import time

from backend.app.repositories.order_export import purge_expired

if __name__ == "__main__":
    print({"已删除过期文件": purge_expired(int(time()))})
