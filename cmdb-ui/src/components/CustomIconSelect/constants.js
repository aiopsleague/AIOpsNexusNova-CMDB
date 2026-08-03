import i18n from '@/lang'

export const iconTypeList = () => [
  // { value: '0', label: '常用' },
  { value: '1', label: i18n.t('customIconSelect.outlined') },
  { value: '2', label: i18n.t('customIconSelect.filled') },
  { value: '3', label: i18n.t('customIconSelect.multicolor') },
  { value: '5', label: i18n.t('customIconSelect.extend') }
]

export const commonIconList = ['changyong-ubuntu',
  'changyong-centos',
  'changyong-changyonglogo45',
  'changyong-pingguo',
  'changyong-windows',
  'changyong-Oracle',
  'changyong-freebsd',
  'changyong-mysql',
  'changyong-fedora',
  'changyong-linux',
  'changyong-sqlite',
  'changyong-memcached',
  'changyong-pingtaiyunweiguanli',
  'changyong-debian',
  'changyong-googlecloud',
  'changyong-mongodb',
  'changyong-redhat',
  'changyong-redis',
  'changyong-amazon',
  'changyong-alibabacloud',
  'changyong-SQLServer',
  'changyong-Sybase',
  'changyong-PostgreSQL',
  'changyong-SUSE',
  'changyong-huawei',
  'changyong-weiruan',
  'changyong-ziyuan40',
  'changyong-tengxunyun',
  'changyong-php',
  'changyong-visual-studio',
  'changyong-java',
  'changyong-ruby',
  'changyong-powershell',
  'changyong-C',
  'changyong-cyuyan',
  'changyong-Python']

export const linearIconList = [
  {
    value: 'database',
    label: 'components.database',
    list: [{
      value: 'icon-xianxing-DB2',
      label: 'DB2'
    }, {
      value: 'icon-xianxing-oracle',
      label: 'Oracle'
    }, {
      value: 'icon-xianxing-informix',
      label: 'Informix'
    }, {
      value: 'icon-xianxing-Sybase',
      label: 'Sybase'
    }, {
      value: 'icon-xianxing-SQLServer',
      label: 'SQLServer'
    }, {
      value: 'icon-xianxing-PostgreSQL',
      label: 'PostgreSQL'
    }, {
      value: 'icon-xianxing-mySQL',
      label: 'mySQL'
    }, {
      value: 'icon-xianxing-access',
      label: 'access'
    }, {
      value: 'icon-xianxing-mongodb',
      label: 'mongodb'
    }, {
      value: 'icon-xianxing-redis',
      label: 'redis'
    }]
  }, {
    value: 'system',
    label: 'components.system',
    list: [{
      value: 'icon-xianxing-Windows',
      label: 'Windows'
    }, {
      value: 'icon-xianxing-Linux',
      label: 'Linux'
    }, {
      value: 'icon-xianxing-unix',
      label: 'Unix'
    }, {
      value: 'icon-xianxing-Mac',
      label: 'Mac'
    }, {
      value: 'icon-xianxing-Ubuntu',
      label: 'Ubuntu'
    }, {
      value: 'icon-xianxing-centos',
      label: 'Centos'
    }, {
      value: 'icon-xianxing-redhat',
      label: 'Redhat'
    }]
  }, {
    value: 'language',
    label: 'components.language',
    list: [{
      value: 'icon-xianxing-python',
      label: 'python'
    }, {
      value: 'icon-xianxing-Java',
      label: 'Java'
    }, {
      value: 'icon-xianxing-c1',
      label: 'C++'
    }, {
      value: 'icon-xianxing-c2',
      label: 'C#'
    }, {
      value: 'icon-xianxing-swift',
      label: 'Swift'
    }, {
      value: 'icon-xianxing-php',
      label: 'PHP'
    }, {
      value: 'icon-xianxing-shell',
      label: 'Shell'
    }, {
      value: 'icon-xianxing-powershell',
      label: 'PowerShell'
    }, {
      value: 'icon-xianxing-bat',
      label: 'Bat'
    }]
  }, {
    value: 'status',
    label: 'components.status',
    list: [{
      value: 'icon-xianxing-yiwen',
      label: '疑问'
    }, {
      value: 'icon-xianxing-zanting',
      label: '暂停'
    }, {
      value: 'icon-xianxing-tianjia',
      label: '添加'
    }, {
      value: 'icon-xianxing-jianqu',
      label: '减去'
    }, {
      value: 'icon-xianxing-quxiao',
      label: '取消'
    }, {
      value: 'icon-xianxing-queren',
      label: '确认'
    }, {
      value: 'icon-xianxing-jinggao',
      label: '警告'
    }, {
      value: 'icon-xianxing-jinzhi',
      label: '禁止'
    }, {
      value: 'icon-xianxing-shuoming',
      label: '说明'
    }, {
      value: 'icon-xianxing-chulizhong',
      label: '处理中'
    }, {
      value: 'icon-xianxing-zaixian',
      label: '在线'
    }, {
      value: 'icon-xianxing-xiaxian',
      label: '下线'
    }]
  }, {
    value: 'icon-xianxing-application',
    label: 'components.commonComponent',
    list: [{
      value: 'icon-xianxing-yilianjie',
      label: '已连接'
    }, {
      value: 'icon-xianxing-weilianjie',
      label: '未连接'
    }, {
      value: 'icon-xianxing-shoucang',
      label: '收藏'
    }, {
      value: 'icon-xianxing-baojing',
      label: '报警'
    }, {
      value: 'icon-xianxing-erweima',
      label: '二维码'
    }, {
      value: 'icon-xianxing-fenzhi',
      label: '分支'
    }, {
      value: 'icon-xianxing-yunshuju',
      label: '云数据'
    }, {
      value: 'icon-xianxing-yunshangchuan',
      label: '云上传'
    }, {
      value: 'icon-xianxing-yunxiazai',
      label: '云下载'
    }, {
      value: 'icon-xianxing-xiaoxi',
      label: '消息'
    }, {
      value: 'icon-xianxing-dingwei',
      label: '定位'
    }, {
      value: 'icon-xianxing-guankan',
      label: '观看'
    }, {
      value: 'icon-xianxing-jinzhiguankan',
      label: '禁止观看'
    }, {
      value: 'icon-xianxing-yirenzheng',
      label: '已认证'
    }, {
      value: 'icon-xianxing-weirenzheng',
      label: '未认证'
    }, {
      value: 'icon-xianxing-biaoqian',
      label: '标签'
    }, {
      value: 'icon-xianxing-yonghu',
      label: '用户'
    }, {
      value: 'icon-xianxing-tianjiayonghu',
      label: '添加用户'
    }, {
      value: 'icon-xianxing-shanchuyonghu',
      label: '删除用户'
    }, {
      value: 'icon-xianxing-qiehuanyonghu',
      label: '切换用户'
    }, {
      value: 'icon-xianxing-weixiu',
      label: '维修'
    }, {
      value: 'icon-xianxing-wuliji',
      label: '物理机'
    }, {
      value: 'icon-xianxing-xuniji',
      label: '虚拟机'
    }, {
      value: 'icon-xianxing-docker',
      label: 'docker'
    }, {
      value: 'icon-xianxing-luyouqi',
      label: '路由器'
    }, {
      value: 'icon-xianxing-jiaohuanji',
      label: '交换机'
    }, {
      value: 'icon-xianxing-fanghuoqiang',
      label: '防火墙'
    }, {
      value: 'icon-xianxing-fuzaijunheng',
      label: '负载均衡'
    }, {
      value: 'icon-xianxing-wangka',
      label: '网卡'
    }, {
      value: 'icon-xianxing-neicun',
      label: '内存'
    }, {
      value: 'icon-xianxing-yingpan',
      label: '硬盘'
    }, {
      value: 'icon-xianxing-bumen',
      label: '部门'
    }, {
      value: 'icon-xianxing-chanpin',
      label: '产品'
    }, {
      value: 'icon-xianxing-dayinji',
      label: '打印机'
    }, {
      value: 'icon-xianxing-chajian',
      label: '插件'
    }, {
      value: 'icon-xianxing-yingyong',
      label: '应用'
    }, {
      value: 'icon-xianxing-nginx',
      label: 'Nginx'
    }, {
      value: 'icon-xianxing-apache',
      label: 'Apache'
    }, {
      value: 'icon-xianxing-tomcat',
      label: 'Tomcat'
    }, {
      value: 'icon-xianxing-aliyun',
      label: '阿里云'
    }, {
      value: 'icon-xianxing-tengxunyun',
      label: '腾讯云'
    }, {
      value: 'icon-xianxing-huaweiyun',
      label: '华为云'
    }, {
      value: 'icon-xianxing-aws',
      label: 'AWS'
    }]
  }, {
    value: 'data',
    label: 'components.data',
    list: [{
      value: 'icon-xianxing-bingzhuangtu',
      label: '饼状图'
    }, {
      value: 'icon-xianxing-huanxingtu',
      label: '环形图'
    }, {
      value: 'icon-xianxing-zhuzhuangtu',
      label: '柱状图'
    }, {
      value: 'icon-xianxing-tiaoxingtu',
      label: '条形图'
    }, {
      value: 'icon-xianxing-mianjitu',
      label: '面积图'
    }, {
      value: 'icon-xianxing-pubutu',
      label: '瀑布图'
    }, {
      value: 'icon-xianxing-xiangxingtu',
      label: '箱型图'
    }, {
      value: 'icon-xianxing-zhexiantu',
      label: '折线图'
    }, {
      value: 'icon-xianxing-dianzhuangtu',
      label: '点状图'
    }, {
      value: 'icon-xianxing-redutu',
      label: '热度图'
    }, {
      value: 'icon-xianxing-shangsheng',
      label: '上升'
    }, {
      value: 'icon-xianxing-xiajiang',
      label: '下降'
    }, {
      value: 'icon-xianxing-gupiaotu',
      label: '股票图'
    }, {
      value: 'icon-xianxing-jijintu',
      label: '基金图'
    }, {
      value: 'icon-xianxing-huakuaitu',
      label: '滑块图'
    }, {
      value: 'icon-xianxing-leidatu',
      label: '雷达图'
    }, {
      value: 'icon-xianxing-shishu',
      label: '整数'
    }, {
      value: 'icon-xianxing-fudianshu',
      label: '浮点数'
    }, {
      value: 'icon-xianxing-wenben',
      label: '文本'
    }, {
      value: 'icon-xianxing-datetime',
      label: 'datetime'
    }, {
      value: 'icon-xianxing-date',
      label: 'date'
    }, {
      value: 'icon-xianxing-time',
      label: 'time'
    }, {
      value: 'icon-xianxing-json',
      label: 'json'
    }]
  }
]

export const fillIconList = [
  {
    value: 'database',
    label: 'components.database',
    list: [{
      value: 'icon-shidi-DB2',
      label: 'DB2'
    }, {
      value: 'icon-shidi-oracle',
      label: 'Oracle'
    }, {
      value: 'icon-shidi-informix',
      label: 'Informix'
    }, {
      value: 'icon-shidi-Sybase',
      label: 'Sybase'
    }, {
      value: 'icon-shidi-SQLServer',
      label: 'SQLServer'
    }, {
      value: 'icon-shidi-PostgreSQL',
      label: 'PostgreSQL'
    }, {
      value: 'icon-shidi-mySQL',
      label: 'mySQL'
    }, {
      value: 'icon-shidi-access',
      label: 'access'
    }, {
      value: 'icon-shidi-mongodb',
      label: 'mongodb'
    }, {
      value: 'icon-shidi-redis',
      label: 'redis'
    }]
  }, {
    value: 'system',
    label: 'components.system',
    list: [{
      value: 'icon-shidi-Windows',
      label: 'Windows'
    }, {
      value: 'icon-shidi-Linux',
      label: 'Linux'
    }, {
      value: 'icon-shidi-unix',
      label: 'Unix'
    }, {
      value: 'icon-shidi-Mac',
      label: 'Mac'
    }, {
      value: 'icon-shidi-Ubuntu',
      label: 'Ubuntu'
    }, {
      value: 'icon-shidi-centos',
      label: 'Centos'
    }, {
      value: 'icon-shidi-redhat',
      label: 'Redhat'
    }]
  }, {
    value: 'language',
    label: 'components.language',
    list: [{
      value: 'icon-shidi-python',
      label: 'python'
    }, {
      value: 'icon-shidi-Java',
      label: 'Java'
    }, {
      value: 'icon-shidi-c1',
      label: 'C++'
    }, {
      value: 'icon-shidi-c2',
      label: 'C#'
    }, {
      value: 'icon-shidi-swift',
      label: 'Swift'
    }, {
      value: 'icon-shidi-php',
      label: 'PHP'
    }, {
      value: 'icon-shidi-shell',
      label: 'Shell'
    }, {
      value: 'icon-shidi-powershell',
      label: 'PowerShell'
    }, {
      value: 'icon-shidi-bat',
      label: 'Bat'
    }]
  }, {
    value: 'status',
    label: 'components.status',
    list: [{
      value: 'icon-shidi-yiwen',
      label: '疑问'
    }, {
      value: 'icon-shidi-zanting',
      label: '暂停'
    }, {
      value: 'icon-shidi-tianjia',
      label: '添加'
    }, {
      value: 'icon-shidi-jianqu',
      label: '减去'
    }, {
      value: 'icon-shidi-quxiao',
      label: '取消'
    }, {
      value: 'icon-shidi-queren',
      label: '确认'
    }, {
      value: 'icon-shidi-jinggao',
      label: '警告'
    }, {
      value: 'icon-shidi-jinzhi',
      label: '禁止'
    }, {
      value: 'icon-shidi-shuoming',
      label: '说明'
    }, {
      value: 'icon-shidi-chulizhong',
      label: '处理中'
    }, {
      value: 'icon-shidi-zaixian',
      label: '在线'
    }, {
      value: 'icon-shidi-xiaxian',
      label: '下线'
    }]
  }, {
    value: 'icon-shidi-application',
    label: 'components.commonComponent',
    list: [{
      value: 'icon-shidi-yilianjie',
      label: '已连接'
    }, {
      value: 'icon-shidi-weilianjie',
      label: '未连接'
    }, {
      value: 'icon-shidi-shoucang',
      label: '收藏'
    }, {
      value: 'icon-shidi-baojing',
      label: '报警'
    }, {
      value: 'icon-shidi-erweima',
      label: '二维码'
    }, {
      value: 'icon-shidi-fenzhi',
      label: '分支'
    }, {
      value: 'icon-shidi-yunshuju',
      label: '云数据'
    }, {
      value: 'icon-shidi-yunshangchuan',
      label: '云上传'
    }, {
      value: 'icon-shidi-yunxiazai',
      label: '云下载'
    }, {
      value: 'icon-shidi-xiaoxi',
      label: '消息'
    }, {
      value: 'icon-shidi-dingwei',
      label: '定位'
    }, {
      value: 'icon-shidi-guankan',
      label: '观看'
    }, {
      value: 'icon-shidi-jinzhiguankan',
      label: '禁止观看'
    }, {
      value: 'icon-shidi-yirenzheng',
      label: '已认证'
    }, {
      value: 'icon-shidi-weirenzheng',
      label: '未认证'
    }, {
      value: 'icon-shidi-biaoqian',
      label: '标签'
    }, {
      value: 'icon-shidi-yonghu',
      label: '用户'
    }, {
      value: 'icon-shidi-tianjiayonghu',
      label: '添加用户'
    }, {
      value: 'icon-shidi-shanchuyonghu',
      label: '删除用户'
    }, {
      value: 'icon-shidi-qiehuanyonghu',
      label: '切换用户'
    }, {
      value: 'icon-shidi-weixiu',
      label: '维修'
    }, {
      value: 'icon-shidi-wuliji',
      label: '物理机'
    }, {
      value: 'icon-shidi-xuniji',
      label: '虚拟机'
    }, {
      value: 'icon-shidi-docker',
      label: 'docker'
    }, {
      value: 'icon-shidi-luyouqi',
      label: '路由器'
    }, {
      value: 'icon-shidi-jiaohuanji',
      label: '交换机'
    }, {
      value: 'icon-shidi-fanghuoqiang',
      label: '防火墙'
    }, {
      value: 'icon-shidi-fuzaijunheng',
      label: '负载均衡'
    }, {
      value: 'icon-shidi-wangka',
      label: '网卡'
    }, {
      value: 'icon-shidi-neicun',
      label: '内存'
    }, {
      value: 'icon-shidi-yingpan',
      label: '硬盘'
    }, {
      value: 'icon-shidi-bumen',
      label: '部门'
    }, {
      value: 'icon-shidi-chanpin',
      label: '产品'
    }, {
      value: 'icon-shidi-dayinji',
      label: '打印机'
    }, {
      value: 'icon-shidi-chajian',
      label: '插件'
    }, {
      value: 'icon-shidi-yingyong',
      label: '应用'
    }, {
      value: 'icon-shidi-nginx',
      label: 'Nginx'
    }, {
      value: 'icon-shidi-apache',
      label: 'Apache'
    }, {
      value: 'icon-shidi-tomcat',
      label: 'Tomcat'
    }, {
      value: 'icon-shidi-aliyun',
      label: '阿里云'
    }, {
      value: 'icon-shidi-tengxunyun',
      label: '腾讯云'
    }, {
      value: 'icon-shidi-huaweiyun',
      label: '华为云'
    }, {
      value: 'icon-shidi-aws',
      label: 'AWS'
    }]
  }, {
    value: 'data',
    label: 'components.data',
    list: [{
      value: 'icon-shidi-bingzhuangtu',
      label: '饼状图'
    }, {
      value: 'icon-shidi-huanxingtu',
      label: '环形图'
    }, {
      value: 'icon-shidi-zhuzhuangtu',
      label: '柱状图'
    }, {
      value: 'icon-shidi-tiaoxingtu',
      label: '条形图'
    }, {
      value: 'icon-shidi-mianjitu',
      label: '面积图'
    }, {
      value: 'icon-shidi-pubutu',
      label: '瀑布图'
    }, {
      value: 'icon-shidi-xiangxingtu',
      label: '箱型图'
    }, {
      value: 'icon-shidi-zhexiantu',
      label: '折线图'
    }, {
      value: 'icon-shidi-dianzhuangtu',
      label: '点状图'
    }, {
      value: 'icon-shidi-redutu',
      label: '热度图'
    }, {
      value: 'icon-shidi-shangsheng',
      label: '上升'
    }, {
      value: 'icon-shidi-xiajiang',
      label: '下降'
    }, {
      value: 'icon-shidi-gupiaotu',
      label: '股票图'
    }, {
      value: 'icon-shidi-jijintu',
      label: '基金图'
    }, {
      value: 'icon-shidi-huakuaitu',
      label: '滑块图'
    }, {
      value: 'icon-shidi-leidatu',
      label: '雷达图'
    }, {
      value: 'icon-shidi-shishu',
      label: '整数'
    }, {
      value: 'icon-shidi-fudianshu',
      label: '浮点数'
    }, {
      value: 'icon-shidi-wenben',
      label: '文本'
    }, {
      value: 'icon-shidi-datetime',
      label: 'datetime'
    }, {
      value: 'icon-shidi-date',
      label: 'date'
    }, {
      value: 'icon-shidi-time',
      label: 'time'
    }, {
      value: 'icon-shidi-json',
      label: 'json'
    }]
  }
]

export const extendIconList = [
  {
    value: 'database',
    label: 'components.database',
    list: [
      { value: 'icon-hdfs-copy', label: 'hdfs-copy' },
      { value: 'icon-hadoop', label: 'hadoop' },
      { value: 'icon-hbase-text', label: 'hbase-text' },
      { value: 'icon-polardb', label: 'polardb' },
      { value: 'icon-tidb-red', label: 'tidb-red' },
      { value: 'icon-oraclelinux', label: 'oraclelinux' },
      { value: 'icon-mongodb-simple', label: 'mongodb-simple' },
      { value: 'icon-opengauss', label: 'opengauss' },
      { value: 'icon-storage', label: 'storage' },
      { value: 'icon-tdb', label: 'tdb' },
      { value: 'icon-database', label: 'database' },
      { value: 'icon-sql', label: 'sql' },
      { value: 'icon-neo4j', label: 'neo4j' },
      { value: 'icon-mysql', label: 'mysql' },
      { value: 'icon-databaseplus-fill', label: 'databaseplus-fill' },
      { value: 'icon-database-fill', label: 'database-fill' },
      { value: 'icon-access', label: 'access' },
      { value: 'icon-sql-outline', label: 'sql-outline' },
      { value: 'icon-rdsmariadb', label: 'rdsmariadb' },
      { value: 'icon-cassandra', label: 'cassandra' },
      { value: 'icon-tidb', label: 'tidb' },
      { value: 'icon-oracle', label: 'oracle' },
      { value: 'icon-postgresql', label: 'postgresql' },
      { value: 'icon-redis', label: 'redis' },
      { value: 'icon-apachespark', label: 'apachespark' },
      { value: 'icon-mongodb', label: 'mongodb' },
      { value: 'icon-elasticsearch', label: 'elasticsearch' },
      { value: 'icon-db2', label: 'db2' },
      { value: 'icon-spark', label: 'spark' },
      { value: 'icon-hbase', label: 'hbase' },
      { value: 'icon-hive', label: 'hive' },
      { value: 'icon-gaussdb', label: 'gaussdb' },
      { value: 'icon-etcd', label: 'etcd' },
      { value: 'icon-sqlite', label: 'sqlite' },
      { value: 'icon-couchdb', label: 'couchdb' },
      { value: 'icon-oceanbase', label: 'oceanbase' },
      { value: 'icon-Influxdb', label: 'Influxdb' },
      { value: 'icon-apachekylin', label: 'apachekylin' },
      { value: 'icon-prometheus1', label: 'prometheus1' },
      { value: 'icon-clickhouse', label: 'clickhouse' },
      { value: 'icon-datasource', label: 'datasource' },
      { value: 'icon-sqlserver', label: 'sqlserver' },
      { value: 'icon-goldengate', label: 'goldengate' },
      { value: 'icon-kafka', label: 'kafka' },
      { value: 'icon-prometheus', label: 'prometheus' },
    ]
  },
  {
    value: 'system',
    label: 'components.system',
    list: [
      { value: 'icon-mobile', label: 'mobile' },
      { value: 'icon-pc', label: 'pc' },
      { value: 'icon-archlinux', label: 'archlinux' },
      { value: 'icon-os', label: 'os' },
      { value: 'icon-oopeneuler', label: 'oopeneuler' },
      { value: 'icon-kernel', label: 'kernel' },
      { value: 'icon-fedora', label: 'fedora' },
      { value: 'icon-almalinux-icon', label: 'almalinux-icon' },
      { value: 'icon-rockylinux', label: 'rockylinux' },
      { value: 'icon-other-os', label: 'other-os' },
      { value: 'icon-gnome', label: 'gnome' },
      { value: 'icon-debian', label: 'debian' },
      { value: 'icon-android', label: 'android' },
      { value: 'icon-ios', label: 'ios' },
      { value: 'icon-os-fill', label: 'os-fill' },
      { value: 'icon-apple', label: 'apple' },
      { value: 'icon-apple-fill', label: 'apple-fill' },
      { value: 'icon-microsoft', label: 'microsoft' },
      { value: 'icon-microsoft-windows', label: 'microsoft-windows' },
      { value: 'icon-macos', label: 'macos' },
      { value: 'icon-alpine', label: 'alpine' },
      { value: 'icon-centos', label: 'centos' },
      { value: 'icon-archlinux-with-title', label: 'archlinux-with-title' },
      { value: 'icon-freebsd', label: 'freebsd' },
      { value: 'icon-windows', label: 'windows' },
      { value: 'icon-ubuntu', label: 'ubuntu' },
      { value: 'icon-redhat', label: 'redhat' },
      { value: 'icon-linux', label: 'linux' },
    ]
  },
  {
    value: 'language',
    label: 'components.language',
    list: [
      { value: 'icon-tex', label: 'tex' },
      { value: 'icon-language-javascript', label: 'language-javascript' },
      { value: 'icon-language-html', label: 'language-html' },
      { value: 'icon-language-java', label: 'language-java' },
      { value: 'icon-language-kotlin', label: 'language-kotlin' },
      { value: 'icon-language-csharp', label: 'language-csharp' },
      { value: 'icon-language-cplusplus', label: 'language-cplusplus' },
      { value: 'icon-language-rust', label: 'language-rust' },
      { value: 'icon-language-php', label: 'language-php' },
      { value: 'icon-markdown', label: 'markdown' },
      { value: 'icon-language-c', label: 'language-c' },
      { value: 'icon-language-css', label: 'language-css' },
      { value: 'icon-blockchain-text', label: 'blockchain-text' },
      { value: 'icon-jquery', label: 'jquery' },
      { value: 'icon-latex', label: 'latex' },
      { value: 'icon-language-golang', label: 'language-golang' },
      { value: 'icon-language-typescript', label: 'language-typescript' },
      { value: 'icon-language-python', label: 'language-python' },
      { value: 'icon-bash', label: 'bash' },
    ]
  },
  {
    value: 'devops',
    label: 'customIconSelect.devops',
    list: [
      { value: 'icon-zabbix-line', label: 'zabbix-line' },
      { value: 'icon-kubesphere', label: 'kubesphere' },
      { value: 'icon-rancher', label: 'rancher' },
      { value: 'icon-saltstack', label: 'saltstack' },
      { value: 'icon-chef', label: 'chef' },
      { value: 'icon-devops-circle', label: 'devops-circle' },
      { value: 'icon-opentelemetry', label: 'opentelemetry' },
      { value: 'icon-puppet', label: 'puppet' },
      { value: 'icon-logstash', label: 'logstash' },
      { value: 'icon-kibana', label: 'kibana' },
      { value: 'icon-elk', label: 'elk' },
      { value: 'icon-skywalking', label: 'skywalking' },
      { value: 'icon-zabbix', label: 'zabbix' },
      { value: 'icon-zabbix-outline', label: 'zabbix-outline' },
      { value: 'icon-sealos', label: 'sealos' },
      { value: 'icon-harbor', label: 'harbor' },
      { value: 'icon-cncf', label: 'cncf' },
      { value: 'icon-container-cluster', label: 'container-cluster' },
      { value: 'icon-open-falcon', label: 'open-falcon' },
      { value: 'icon-teleport', label: 'teleport' },
      { value: 'icon-cicd', label: 'cicd' },
      { value: 'icon-microservice', label: 'microservice' },
      { value: 'icon-spring-boot', label: 'spring-boot' },
      { value: 'icon-iis', label: 'iis' },
      { value: 'icon-jumpserver', label: 'jumpserver' },
      { value: 'icon-github', label: 'github' },
      { value: 'icon-github-fill', label: 'github-fill' },
      { value: 'icon-git1', label: 'git1' },
      { value: 'icon-vite', label: 'vite' },
      { value: 'icon-vuepress', label: 'vuepress' },
      { value: 'icon-webpack', label: 'webpack' },
      { value: 'icon-stack', label: 'stack' },
      { value: 'icon-kubesphere-with-title', label: 'kubesphere-with-title' },
      { value: 'icon-azuredevops', label: 'azuredevops' },
      { value: 'icon-terraform', label: 'terraform' },
      { value: 'icon-ansible', label: 'ansible' },
      { value: 'icon-helm', label: 'helm' },
      { value: 'icon-rancher-long', label: 'rancher-long' },
      { value: 'icon-portainer', label: 'portainer' },
      { value: 'icon-devops-long', label: 'devops-long' },
      { value: 'icon-kubernetes', label: 'kubernetes' },
      { value: 'icon-fastapi', label: 'fastapi' },
      { value: 'icon-git', label: 'git' },
      { value: 'icon-vuetify', label: 'vuetify' },
      { value: 'icon-zabbix-with-title', label: 'zabbix-with-title' },
      { value: 'icon-jenkins', label: 'jenkins' },
      { value: 'icon-gin', label: 'gin' },
      { value: 'icon-flask', label: 'flask' },
      { value: 'icon-nginx', label: 'nginx' },
      { value: 'icon-apache', label: 'apache' },
      { value: 'icon-docker', label: 'docker' },
      { value: 'icon-gitlab', label: 'gitlab' },
      { value: 'icon-grafana', label: 'grafana' },
      { value: 'icon-devops', label: 'devops' },
      { value: 'icon-gitee', label: 'gitee' },
      { value: 'icon-django', label: 'django' },
      { value: 'icon-vue', label: 'vue' },
      { value: 'icon-beego', label: 'beego' },
      { value: 'icon-react', label: 'react' },
    ]
  },
  {
    value: 'cloud',
    label: 'components.cloud',
    list: [
      { value: 'icon-cloudnative', label: 'cloudnative' },
      { value: 'icon-microsoftazure', label: 'microsoftazure' },
      { value: 'icon-amazon', label: 'amazon' },
      { value: 'icon-azure', label: 'azure' },
      { value: 'icon-alibaba', label: 'alibaba' },
      { value: 'icon-microsoft-azure', label: 'microsoft-azure' },
      { value: 'icon-firebase', label: 'firebase' },
      { value: 'icon-nextcloud', label: 'nextcloud' },
      { value: 'icon-cloud', label: 'cloud' },
    ]
  },
  {
    value: 'itsm',
    label: 'customIconSelect.itsm',
    list: [
      { value: 'icon-operation-specification', label: 'operation-specification' },
      { value: 'icon-service-desk', label: 'service-desk' },
      { value: 'icon-practice', label: 'practice' },
      { value: 'icon-strategy', label: 'strategy' },
      { value: 'icon-strategy-filled', label: 'strategy-filled' },
      { value: 'icon-ha', label: 'ha' },
      { value: 'icon-high-availability', label: 'high-availability' },
      { value: 'icon-risk', label: 'risk' },
      { value: 'icon-continuity-fill', label: 'continuity-fill' },
      { value: 'icon-continuity', label: 'continuity' },
      { value: 'icon-availability', label: 'availability' },
      { value: 'icon-capacity', label: 'capacity' },
      { value: 'icon-capacity-outline', label: 'capacity-outline' },
      { value: 'icon-performance-outline', label: 'performance-outline' },
      { value: 'icon-performance', label: 'performance' },
      { value: 'icon-capacity-filled', label: 'capacity-filled' },
      { value: 'icon-incident', label: 'incident' },
      { value: 'icon-sla', label: 'sla' },
      { value: 'icon-slack', label: 'slack' },
      { value: 'icon-operation-management-framework', label: 'operation-management-framework' },
      { value: 'icon-operation-management', label: 'operation-management' },
      { value: 'icon-specification', label: 'specification' },
      { value: 'icon-operation', label: 'operation' },
      { value: 'icon-cmdb', label: 'cmdb' },
      { value: 'icon-cmdb-fill', label: 'cmdb-fill' },
      { value: 'icon-plan', label: 'plan' },
      { value: 'icon-problem', label: 'problem' },
      { value: 'icon-itil', label: 'itil' },
      { value: 'icon-itss', label: 'itss' },
      { value: 'icon-knowledge', label: 'knowledge' },
      { value: 'icon-change', label: 'change' },
      { value: 'icon-itsm', label: 'itsm' },
      { value: 'icon-release', label: 'release' },
      { value: 'icon-configuration', label: 'configuration' },
      { value: 'icon-request', label: 'request' },
      { value: 'icon-incident-line', label: 'incident-line' },
      { value: 'icon-governance', label: 'governance' },
      { value: 'icon-translate', label: 'translate' },
    ]
  },
  {
    value: 'ai_data',
    label: 'customIconSelect.aiData',
    list: [
      { value: 'icon-datastructure', label: 'datastructure' },
      { value: 'icon-algorithm', label: 'algorithm' },
      { value: 'icon-datascience', label: 'datascience' },
      { value: 'icon-datascience-line', label: 'datascience-line' },
      { value: 'icon-datagrip', label: 'datagrip' },
      { value: 'icon-echarts', label: 'echarts' },
      { value: 'icon-pandas', label: 'pandas' },
      { value: 'icon-finebi', label: 'finebi' },
      { value: 'icon-chatgpt', label: 'chatgpt' },
      { value: 'icon-llm', label: 'llm' },
      { value: 'icon-anaconda', label: 'anaconda' },
      { value: 'icon-ai', label: 'ai' },
      { value: 'icon-aibrain', label: 'aibrain' },
      { value: 'icon-deep-learning', label: 'deep-learning' },
      { value: 'icon-antv', label: 'antv' },
      { value: 'icon-sympy', label: 'sympy' },
      { value: 'icon-d3js', label: 'd3js' },
      { value: 'icon-thingjs', label: 'thingjs' },
      { value: 'icon-threejs', label: 'threejs' },
      { value: 'icon-scipy', label: 'scipy' },
      { value: 'icon-datascience-fill', label: 'datascience-fill' },
      { value: 'icon-highcharts', label: 'highcharts' },
      { value: 'icon-matplotlib', label: 'matplotlib' },
      { value: 'icon-pandas-with-title', label: 'pandas-with-title' },
      { value: 'icon-finebi-with-title', label: 'finebi-with-title' },
      { value: 'icon-numpy', label: 'numpy' },
      { value: 'icon-tableau', label: 'tableau' },
      { value: 'icon-pytorch', label: 'pytorch' },
      { value: 'icon-pentaho', label: 'pentaho' },
      { value: 'icon-plotly', label: 'plotly' },
      { value: 'icon-tensorflow', label: 'tensorflow' },
      { value: 'icon-echarts-with-title', label: 'echarts-with-title' },
      { value: 'icon-scikitlearn', label: 'scikitlearn' },
      { value: 'icon-datagrip-with-title', label: 'datagrip-with-title' },
      { value: 'icon-kettle', label: 'kettle' },
      { value: 'icon-powerbi', label: 'powerbi' },
      { value: 'icon-algorithm-line', label: 'algorithm-line' },
    ]
  },
  {
    value: 'network',
    label: 'customIconSelect.network',
    list: [
      { value: 'icon-security', label: 'security' },
      { value: 'icon-connection', label: 'connection' },
      { value: 'icon-wifi', label: 'wifi' },
      { value: 'icon-network', label: 'network' },
      { value: 'icon-ssl', label: 'ssl' },
      { value: 'icon-domain', label: 'domain' },
      { value: 'icon-ssl-outline', label: 'ssl-outline' },
      { value: 'icon-infosec', label: 'infosec' },
      { value: 'icon-vpn-outline', label: 'vpn-outline' },
      { value: 'icon-vpn-fill', label: 'vpn-fill' },
      { value: 'icon-iot-fill', label: 'iot-fill' },
      { value: 'icon-http', label: 'http' },
      { value: 'icon-api', label: 'api' },
      { value: 'icon-ssl-fill', label: 'ssl-fill' },
      { value: 'icon-proxy', label: 'proxy' },
      { value: 'icon-clash', label: 'clash' },
      { value: 'icon-vpn-svgrepo-com', label: 'vpn-svgrepo-com' },
      { value: 'icon-https', label: 'https' },
      { value: 'icon-openvpn', label: 'openvpn' },
      { value: 'icon-certified', label: 'certified' },
      { value: 'icon-iot', label: 'iot' },
    ]
  },
  {
    value: 'tools',
    label: 'customIconSelect.tools',
    list: [
      { value: 'icon-left-template', label: 'left-template' },
      { value: 'icon-frame', label: 'frame' },
      { value: 'icon-kb', label: 'kb' },
      { value: 'icon-opsmgt', label: 'opsmgt' },
      { value: 'icon-parameter', label: 'parameter' },
      { value: 'icon-catalog', label: 'catalog' },
      { value: 'icon-demo-outline', label: 'demo-outline' },
      { value: 'icon-demo', label: 'demo' },
      { value: 'icon-design', label: 'design' },
      { value: 'icon-introduction', label: 'introduction' },
      { value: 'icon-chart-line', label: 'chart-line' },
      { value: 'icon-mini-program', label: 'mini-program' },
      { value: 'icon-mini-program-line', label: 'mini-program-line' },
      { value: 'icon-study', label: 'study' },
      { value: 'icon-lowcode', label: 'lowcode' },
      { value: 'icon-extension-fill', label: 'extension-fill' },
      { value: 'icon-extension', label: 'extension' },
      { value: 'icon-discover', label: 'discover' },
      { value: 'icon-guidance', label: 'guidance' },
      { value: 'icon-tools', label: 'tools' },
      { value: 'icon-workspace', label: 'workspace' },
      { value: 'icon-education', label: 'education' },
      { value: 'icon-code-review', label: 'code-review' },
      { value: 'icon-admin', label: 'admin' },
      { value: 'icon-workspace-color', label: 'workspace-color' },
      { value: 'icon-mindmap', label: 'mindmap' },
      { value: 'icon-wiki', label: 'wiki' },
      { value: 'icon-wikipedia', label: 'wikipedia' },
      { value: 'icon-template', label: 'template' },
      { value: 'icon-emacs', label: 'emacs' },
      { value: 'icon-vim', label: 'vim' },
      { value: 'icon-table', label: 'table' },
      { value: 'icon-office', label: 'office' },
      { value: 'icon-chart', label: 'chart' },
      { value: 'icon-atom', label: 'atom' },
      { value: 'icon-office-word', label: 'office-word' },
      { value: 'icon-office-excel', label: 'office-excel' },
      { value: 'icon-office-pptx', label: 'office-pptx' },
      { value: 'icon-w3c', label: 'w3c' },
      { value: 'icon-leetcode', label: 'leetcode' },
      { value: 'icon-safari', label: 'safari' },
      { value: 'icon-game', label: 'game' },
      { value: 'icon-gitbook', label: 'gitbook' },
      { value: 'icon-project', label: 'project' },
      { value: 'icon-development', label: 'development' },
      { value: 'icon-opensource-fill', label: 'opensource-fill' },
      { value: 'icon-tool', label: 'tool' },
      { value: 'icon-color', label: 'color' },
      { value: 'icon-font-size', label: 'font-size' },
      { value: 'icon-position', label: 'position' },
      { value: 'icon-drive', label: 'drive' },
      { value: 'icon-stackoverflow', label: 'stackoverflow' },
      { value: 'icon-programming', label: 'programming' },
      { value: 'icon-opensource-line', label: 'opensource-line' },
      { value: 'icon-flat-ui', label: 'flat-ui' },
      { value: 'icon-google-drive', label: 'google-drive' },
      { value: 'icon-microsoft-authenticator', label: 'microsoft-authenticator' },
      { value: 'icon-edge', label: 'edge' },
      { value: 'icon-terminal', label: 'terminal' },
      { value: 'icon-chrome', label: 'chrome' },
      { value: 'icon-firefox', label: 'firefox' },
      { value: 'icon-xmind', label: 'xmind' },
      { value: 'icon-vscode', label: 'vscode' },
      { value: 'icon-antdesign', label: 'antdesign' },
      { value: 'icon-code', label: 'code' },
      { value: 'icon-backend', label: 'backend' },
      { value: 'icon-blackcode', label: 'blackcode' },
      { value: 'icon-frontend', label: 'frontend' },
    ]
  },
  {
    value: 'social',
    label: 'customIconSelect.social',
    list: [
      { value: 'icon-twitterx', label: 'twitterx' },
      { value: 'icon-mail', label: 'mail' },
      { value: 'icon-dingtalk', label: 'dingtalk' },
      { value: 'icon-instagram', label: 'instagram' },
      { value: 'icon-whatsapp', label: 'whatsapp' },
      { value: 'icon-wechat', label: 'wechat' },
      { value: 'icon-wechat-fill', label: 'wechat-fill' },
      { value: 'icon-googleplus', label: 'googleplus' },
      { value: 'icon-telegram', label: 'telegram' },
      { value: 'icon-qq', label: 'qq' },
      { value: 'icon-email', label: 'email' },
      { value: 'icon-facebook', label: 'facebook' },
      { value: 'icon-google', label: 'google' },
      { value: 'icon-twitter', label: 'twitter' },
      { value: 'icon-skype', label: 'skype' },
      { value: 'icon-reddit', label: 'reddit' },
      { value: 'icon-tiktok', label: 'tiktok' },
      { value: 'icon-youtube', label: 'youtube' },
      { value: 'icon-eleme', label: 'eleme' },
    ]
  },
  {
    value: 'other',
    label: 'customIconSelect.other',
    list: [
      { value: 'icon-cryptocurrency-wallet', label: 'cryptocurrency-wallet' },
      { value: 'icon-btc', label: 'btc' },
      { value: 'icon-eth', label: 'eth' },
      { value: 'icon-cryptocurrency', label: 'cryptocurrency' },
      { value: 'icon-xch', label: 'xch' },
      { value: 'icon-finance-fill', label: 'finance-fill' },
      { value: 'icon-data-analysis', label: 'data-analysis' },
      { value: 'icon-ethereum', label: 'ethereum' },
      { value: 'icon-blockchain-stack', label: 'blockchain-stack' },
      { value: 'icon-blockchain', label: 'blockchain' },
    ]
  },
]

export const multicolorIconList = [
  {
    value: 'database',
    label: 'components.database',
    list: [{
      value: 'caise-TIDB',
      label: 'TIDB'
    }, {
      value: 'caise-dameng',
      label: '达梦'
    }, {
      value: 'caise-kingbase',
      label: 'KingBase'
    }, {
      value: 'caise-TDSQL',
      label: 'TDSQL'
    }, {
      value: 'caise-DB2',
      label: 'DB2'
    }, {
      value: 'caise-oracle',
      label: 'Oracle'
    }, {
      value: 'caise-informix',
      label: 'Informix'
    }, {
      value: 'caise-Sybase',
      label: 'Sybase'
    }, {
      value: 'caise-SQLServer',
      label: 'SQLServer'
    }, {
      value: 'caise-PostgreSQL',
      label: 'PostgreSQL'
    }, {
      value: 'caise-mySQL',
      label: 'mySQL'
    }, {
      value: 'caise-access',
      label: 'access'
    }, {
      value: 'caise-mongodb',
      label: 'mongodb'
    }, {
      value: 'caise-redis',
      label: 'redis'
    }]
  }, {
    value: 'cloud',
    label: 'components.cloud',
    list: [{
      value: 'AWS',
      label: 'AWS'
    }, {
      value: 'Azure',
      label: 'Azure'
    }, {
      value: 'Google_Cloud_Platform',
      label: 'Google Cloud Platform'
    }, {
      value: 'Alibaba_Cloud',
      label: '阿里云'
    }, {
      value: 'Huawei_Cloud',
      label: '华为云'
    }, {
      value: 'Tencent_Cloud',
      label: '腾讯云'
    }, {
      value: 'UCloud',
      label: 'UCloud'
    }, {
      value: 'Ctyun',
      label: '天翼云'
    }, {
      value: 'ECloud',
      label: '移动云'
    }, {
      value: 'JDCloud',
      label: '京东云'
    }, {
      value: 'Bytecloud',
      label: '字节云'
    }, {
      value: 'OpenStack',
      label: 'OpenStack'
    }, {
      value: 'ZStack',
      label: 'ZStack'
    }, {
      value: 'Nutanix',
      label: 'Nutanix'
    }]
  }, {
    value: 'system',
    label: 'components.system',
    list: [{
      value: 'ciase-aix',
      label: 'aix'
    }, {
      value: 'caise-Windows',
      label: 'Windows'
    }, {
      value: 'caise-Linux',
      label: 'Linux'
    }, {
      value: 'caise-unix',
      label: 'Unix'
    }, {
      value: 'caise-Mac',
      label: 'Mac'
    }, {
      value: 'caise-Ubuntu',
      label: 'Ubuntu'
    }, {
      value: 'caise-centos',
      label: 'Centos'
    }, {
      value: 'caise-redhat',
      label: 'Redhat'
    }]
  }, {
    value: 'language',
    label: 'components.language',
    list: [{
      value: 'caise-python',
      label: 'python'
    }, {
      value: 'caise-Java',
      label: 'Java'
    }, {
      value: 'caise-c1',
      label: 'C++'
    }, {
      value: 'caise-c2',
      label: 'C#'
    }, {
      value: 'caise-swift',
      label: 'Swift'
    }, {
      value: 'caise-php',
      label: 'PHP'
    }, {
      value: 'caise-shell',
      label: 'Shell'
    }, {
      value: 'caise-powershell',
      label: 'PowerShell'
    }, {
      value: 'caise-bat',
      label: 'Bat'
    }]
  }, {
    value: 'status',
    label: 'components.status',
    list: [{
      value: 'caise-yiwen',
      label: '疑问'
    }, {
      value: 'caise-zanting',
      label: '暂停'
    }, {
      value: 'caise-tianjia',
      label: '添加'
    }, {
      value: 'caise-jianqu',
      label: '减去'
    }, {
      value: 'caise-quxiao',
      label: '取消'
    }, {
      value: 'caise-queren',
      label: '确认'
    }, {
      value: 'caise-jinggao',
      label: '警告'
    }, {
      value: 'caise-jinzhi',
      label: '禁止'
    }, {
      value: 'caise-shuoming',
      label: '说明'
    }, {
      value: 'caise-chulizhong',
      label: '处理中'
    }, {
      value: 'caise-zaixian',
      label: '在线'
    }, {
      value: 'caise-xiaxian',
      label: '下线'
    }]
  }, {
    value: 'caise-application',
    label: 'components.commonComponent',
    list: [{
      value: 'caise-websphere',
      label: 'WebSphere'
    }, {
      value: 'caise-vps',
      label: 'VPS'
    }, {
      value: 'caise-F5',
      label: 'F5'
    }, {
      value: 'caise-HAProxy',
      label: 'HAProxy'
    }, {
      value: 'caise-kafka',
      label: 'kafka'
    }, {
      value: 'caise-dongfangtong',
      label: '东方通'
    }, {
      value: 'cmdb-vcenter',
      label: 'VCenter'
    }, {
      value: 'ops-KVM',
      label: 'KVM'
    }, {
      value: 'caise-JBoss',
      label: 'JBoss'
    }, {
      value: 'caise-weblogic',
      label: 'WebLogic'
    }, {
      value: 'caise-disk_array',
      label: '磁盘阵列'
    }, {
      value: 'caise-fiber',
      label: '光纤交换机'
    }, {
      value: 'caise-bandwidth_line',
      label: '带宽线路'
    }, {
      value: 'caise-pc',
      label: 'PC'
    }, {
      value: 'caise-rack',
      label: '机柜'
    }, {
      value: 'caise-computer_room',
      label: '机房'
    }, {
      value: 'caise-ip_address',
      label: 'ip地址'
    }, {
      value: 'caise_pool',
      label: 'ip池'
    }, {
      value: 'caise-storage_volume1',
      label: '存储卷'
    }, {
      value: 'caise-virtualization',
      label: '虚拟化'
    }, {
      value: 'caise-business',
      label: '业务'
    }, {
      value: 'caise-database',
      label: '数据库'
    }, {
      value: 'caise-middleware',
      label: '中间件'
    }, {
      value: 'caise-websever',
      label: 'websever'
    }, {
      value: 'caise-message_queue',
      label: '消息队列'
    }, {
      value: 'caise-load_balancing',
      label: '负载均衡'
    }, {
      value: 'caise-storage_device',
      label: '存储设备'
    }, {
      value: 'caise-network_devices',
      label: '网络设备'
    }, {
      value: 'caise-computer',
      label: '计算机'
    }, {
      value: 'caise-hardware',
      label: '硬件设备'
    }, {
      value: 'caise-data_center2',
      label: '数据中心'
    }, {
      value: 'caise-hyperV',
      label: 'hyperV'
    }, {
      value: 'caise-IPAM',
      label: 'IPAM'
    }, {
      value: 'caise-system',
      label: '操作系统'
    }, {
      value: 'caise-public_cloud',
      label: '公有云'
    }, {
      value: 'caise-data_center',
      label: '数据中心'
    }, {
      value: 'caise-folder',
      label: '文件夹'
    }, {
      value: 'caise-resource_pool',
      label: '资源池'
    }, {
      value: 'caise-network',
      label: '网络'
    }, {
      value: 'caise-distributed_switch',
      label: '分布式交换机'
    }, {
      value: 'caise-standard_switch',
      label: '标准式交换机'
    }, {
      value: 'caise-host_cluster',
      label: '主机集群'
    }, {
      value: 'caise-storage_cluster',
      label: '数据存储集群'
    }, {
      value: 'caise-data_storage',
      label: '数据存储'
    }, {
      value: 'caise-yilianjie',
      label: '已连接'
    }, {
      value: 'caise-weilianjie',
      label: '未连接'
    }, {
      value: 'caise-shoucang',
      label: '收藏'
    }, {
      value: 'caise-baojing',
      label: '报警'
    }, {
      value: 'caise-erweima',
      label: '二维码'
    }, {
      value: 'caise-fenzhi',
      label: '分支'
    }, {
      value: 'caise-yunshuju',
      label: '云数据'
    }, {
      value: 'caise-yunshangchuan',
      label: '云上传'
    }, {
      value: 'caise-yunxiazai',
      label: '云下载'
    }, {
      value: 'caise-xiaoxi',
      label: '消息'
    }, {
      value: 'caise-dingwei',
      label: '定位'
    }, {
      value: 'caise-guankan',
      label: '观看'
    }, {
      value: 'caise-jinzhiguankan',
      label: '禁止观看'
    }, {
      value: 'caise-yirenzheng',
      label: '已认证'
    }, {
      value: 'caise-weirenzheng',
      label: '未认证'
    }, {
      value: 'caise-biaoqian',
      label: '标签'
    }, {
      value: 'caise-yonghu',
      label: '用户'
    }, {
      value: 'caise-tianjiayonghu',
      label: '添加用户'
    }, {
      value: 'caise-shanchuyonghu',
      label: '删除用户'
    }, {
      value: 'caise-qiehuanyonghu',
      label: '切换用户'
    }, {
      value: 'caise-weixiu',
      label: '维修'
    }, {
      value: 'caise-wuliji',
      label: '物理机'
    }, {
      value: 'caise-xuniji',
      label: '虚拟机'
    }, {
      value: 'caise-docker',
      label: 'docker'
    }, {
      value: 'caise-luyouqi',
      label: '路由器'
    }, {
      value: 'caise-jiaohuanji',
      label: '交换机'
    }, {
      value: 'caise-fanghuoqiang',
      label: '防火墙'
    }, {
      value: 'caise-fuzaijunheng',
      label: '负载均衡'
    }, {
      value: 'caise-wangka',
      label: '网卡'
    }, {
      value: 'caise-neicun',
      label: '内存'
    }, {
      value: 'caise-yingpan',
      label: '硬盘'
    }, {
      value: 'caise-bumen',
      label: '部门'
    }, {
      value: 'caise-chanpin',
      label: '产品'
    }, {
      value: 'caise-yingyong',
      label: '应用'
    }, {
      value: 'caise-dayinji',
      label: '打印机'
    }, {
      value: 'caise-chajian',
      label: '插件'
    }, {
      value: 'caise-nginx',
      label: 'Nginx'
    }, {
      value: 'caise-apache',
      label: 'Apache'
    }, {
      value: 'caise-tomcat',
      label: 'Tomcat'
    }, {
      value: 'caise-VPC',
      label: 'VPC'
    }, {
      value: 'caise-CDN',
      label: 'CDN'
    }, {
      value: 'caise-OOS',
      label: '对象存储'
    }]
  }, {
    value: 'data',
    label: 'components.data',
    list: [{
      value: 'caise-bingzhuangtu',
      label: '饼状图'
    }, {
      value: 'caise-huanxingtu',
      label: '环形图'
    }, {
      value: 'caise-zhuzhuangtu',
      label: '柱状图'
    }, {
      value: 'caise-tiaoxingtu',
      label: '条形图'
    }, {
      value: 'caise-mianjitu',
      label: '面积图'
    }, {
      value: 'caise-pubutu',
      label: '瀑布图'
    }, {
      value: 'caise-xiangxingtu',
      label: '箱型图'
    }, {
      value: 'caise-zhexiantu',
      label: '折线图'
    }, {
      value: 'caise-dianzhuangtu',
      label: '点状图'
    }, {
      value: 'caise-redutu',
      label: '热度图'
    }, {
      value: 'caise-shangsheng',
      label: '上升'
    }, {
      value: 'caise-xiajiang',
      label: '下降'
    }, {
      value: 'caise-gupiaotu',
      label: '股票图'
    }, {
      value: 'caise-jijintu',
      label: '基金图'
    }, {
      value: 'caise-huakuaitu',
      label: '滑块图'
    }, {
      value: 'caise-leidatu',
      label: '雷达图'
    }, {
      value: 'caise-shishu',
      label: '整数'
    }, {
      value: 'caise-fudianshu',
      label: '浮点数'
    }, {
      value: 'caise-wenben',
      label: '文本'
    }, {
      value: 'caise-datetime',
      label: 'datetime'
    }, {
      value: 'caise-date',
      label: 'date'
    }, {
      value: 'caise-time',
      label: 'time'
    }, {
      value: 'caise-json',
      label: 'json'
    }]
  }
]
