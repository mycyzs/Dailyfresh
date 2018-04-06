from django.core.files.storage import FileSystemStorage
from fdfs_client.client import Fdfs_client


class FdfsStorage(FileSystemStorage):
    # 继承django的save方法，这个方法默认后台存入数据的时候，一些静态文件就会被存储到项目下，
    # 现在的要求是继承django的save方法，把一些静态文件存储到fastdfs文件存储系统中，sdk方法
    # 访问页面的时候，iginx可以从fastdfs下载页面所需的静态文件，并显示在浏览器页面
    def _save(self, name, content):
        client = Fdfs_client('./utils/fdfs/client.conf')
        try:
            #   'Status': 'Upload successed.',
            #   'Remote file_id':'group1/M00/00/00/wKjSolqihW2ATqs4AAAmv27pX4k506.jpg'
            data = content.read()
            data_dict = client.upload_by_buffer(data)
        except Exception as e:
            raise e
        # 检验是否上传成功,json是一个字典的形式
        if data_dict.get('Status') != 'Upload successed.':
            raise Exception('上传失败')
        # 获取文件的id，iginx可以根据id下载静态文件
        path = data_dict.get('Remote file_id')

        return path

    # 重写图片的url方法，把地址拼成iginx直接访问下载图片的地址
    def url(self, name):
        path = 'http://127.0.0.1:8888/' + super().url(name)
        return path
