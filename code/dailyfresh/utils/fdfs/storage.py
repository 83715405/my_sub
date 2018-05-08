from django.core.files.storage import FileSystemStorage
from fdfs_client.client import Fdfs_client


class FdfsStorage(FileSystemStorage):
    def _save(self, name, content):
        '''当用户通过管理后台上传文件时,
        django会调用此方法来保存用户上传到django网站的文件,
        我们可以在此方法中保存用户上传的文件到FastDFS服务器中
        '''
        # todo: 默认保存方式：
        # path = super()._save(name, content)
        # print(path, name)

        # todo: 自定义存储： 保存文件到Fdfs服务器
        client = Fdfs_client('utils/fdfs/client.conf')
        try:
            datas = content.read()
            dict_data = client.upload_by_buffer(datas)  # 上传文件到fdfs
            status = dict_data.get("Status")
            if status == 'Upload successed.':
                # 上传成功
                path = dict_data.get('Remote file_id')
            else:
                raise Exception('上传文件到FastDFS失败,Status不正确')
                # 获取文件id

        except Exception as e:
            print(e)
            raise e  # 不要直接捕获异常, 抛出去由调用者进行处理

        return path

    def url(self, name):
        path = super().url(name)
        return 'http://127.0.0.1:8888/' + path
