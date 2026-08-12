# 《Axiom-Hilbert 智能运维平台 - 统一命名规范》
> 文档版本：V1.0
> 设计理念：整套平台采用 **Axiom-{数学家英文名}** 谱系命名。Axiom（公理）代表运维资源模型、配置基线、治理标准；各子服务选用对应研究领域的数学家命名，语义与业务职责强绑定，形成统一数学体系，摒弃通用词汇（cmdb、discover、event），辨识度高、易于长期演进。

## 一、基础命名格式标准
| 使用场景 | 命名范式 | 规则说明 | 示例 |
| ---- | ---- | ---- | ---- |
| 产品对外正式名称（文档、前端标题、宣传） | `Axiom-{Mathematician}` | 首字母大写，横杠 `-` 分隔 | Axiom-Cantor |
| K8s Service、镜像名、Git仓库、域名、资源标识（kebab-case） | `axiom-{mathematician}` | 全小写，短横线，URL/容器生态兼容 | axiom-cantor |
| Go/Java 模块、结构体、前端组件（大驼峰） | `Axiom{Mathematician}` | 代码内部标识符 | AxiomCantor |
| 数据库、MQ Topic、数据表（snake_case） | `axiom_{mathematician}` | 全小写，下划线分隔 | axiom_cantor |

### 补充约束
1. 所有子组件**不重复使用数学家名称**，主平台名称禁止在子服务复用；
2. Agent、Gateway 等角色后缀追加在名称尾部；
3. API 统一路由前缀：`/api/v1/axiom/{mathematician}`；
4. 配置文件：`axiom-xxx.yaml`；镜像规范：`registry/axiom-xxx:${VERSION}`。

## 二、平台与核心组件完整命名清单
### 2.1 顶层基座平台
**产品名称：Axiom-Hilbert**
- service：`axiom-hilbert`
- module：`AxiomHilbert`

> 释义：
> Hilbert（大卫·希尔伯特），近代公理体系奠基人。平台以其命名，寓意构建一套严谨、自洽、可扩展的运维数据与模型公理底座，统一所有运维资源标准。

---

### 2.2 CMDB 资产配置管理中心
**产品名称：Axiom-Cantor**
- service：`axiom-cantor`
- module：`AxiomCantor`
- database：`axiom_cantor`
- api prefix：`/api/v1/axiom/cantor`

> 释义：
> Cantor（康托尔），集合论创立者。CMDB本质是各类IT资源的集合，管理CI配置项、资源分组、资产台账、对象关系，完美契合集合论思想。

---

### 2.3 自动采集客户端 Agent（主机侧探针）
**产品名称：Axiom-Euler Agent**
- service / 镜像：`axiom-euler-agent`
- module：`AxiomEulerAgent`
- config：`axiom-euler-agent.yaml`

> 释义：
> Euler（欧拉），图论、拓扑学开创者。Agent负责扫描探测节点、发现网络拓扑、采集主机与实例信息，在运维空间中发现节点与连接关系。

---

### 2.4 自动采集上报中心（数据网关）
**产品名称：Axiom-Riemann Gateway**
- service：`axiom-riemann-gateway`
- module：`AxiomRiemannGateway`
- api prefix：`/api/v1/axiom/riemann`

> 释义：
> Riemann（黎曼），分析学、流形理论代表人物。网关接收异构Agent上报数据，完成数据变换、清洗、归一化，将零散原始数据规整为统一模型，流入CMDB。

---

### 2.5 事件管理服务（告警、故障事件、工单）
**产品名称：Axiom-Kolmogorov**
- service：`axiom-kolmogorov`
- module：`AxiomKolmogorov`
- database：`axiom_kolmogorov`
- api prefix：`/api/v1/axiom/kolmogorov`

> 释义：
> Kolmogorov（柯尔莫哥洛夫），概率论、随机过程奠基人。系统故障、指标波动属于随机事件；该模块承载事件接收、告警收敛、故障生命周期管理、事件概率关联分析。

## 三、预留扩展模块命名（后续新增直接复用规范）
1. AIOps 异常检测 & 基线分析中心
产品：Axiom-Gauss
service：`axiom-gauss`
> Gauss（高斯），正态分布、误差分析；用于指标基线、异常阈值、统计分析。

2. 资源拓扑图谱 & 依赖分析引擎
产品：Axiom-Poincaré
service：`axiom-poincare`
> Poincaré（庞加莱），动力学、混沌理论；分析系统动态依赖、故障传导链路。

## 四、完整架构清单（可直接复制到部署文档）
```
【顶层基座】
产品：Axiom-Hilbert
service: axiom-hilbert
module: AxiomHilbert

【四大核心业务组件】
1. CMDB资产中心
对外名称：Axiom-Cantor
service: axiom-cantor
module: AxiomCantor
db: axiom_cantor

2. 自动采集客户端Agent
对外名称：Axiom-Euler Agent
service: axiom-euler-agent
module: AxiomEulerAgent

3. 采集上报网关
对外名称：Axiom-Riemann Gateway
service: axiom-riemann-gateway
module: AxiomRiemannGateway

4. 事件管理中心
对外名称：Axiom-Kolmogorov
service: axiom-kolmogorov
module: AxiomKolmogorov
db: axiom_kolmogorov
```

# README 配套简介文案（可直接粘贴进项目根目录README.md）
## Axiom-Hilbert
Axiom-Hilbert 是面向多云混合架构的新一代智能运维底座。
命名体系源自数学公理体系与经典数学家谱系：
- **Axiom**：公理，代表平台定义统一的IT资源模型、配置基线与运维治理标准；
- **Hilbert**：希尔伯特，公理体系奠基人，象征平台具备严谨、可扩展、自洽的数据模型底座。

### 核心子系统谱系释义
- **Axiom-Cantor**：CMDB资产配置中心。以集合论创始人康托尔命名，管理所有IT资产配置项、资源台账与对象关系集合。
- **Axiom-Euler Agent**：自动采集客户端。以图论开创者欧拉命名，部署于目标节点，完成资源探测、拓扑发现与原始数据采集。
- **Axiom-Riemann Gateway**：采集上报中心。以黎曼命名，负责接收多源采集数据，完成清洗、转换、归一化，标准化写入CMDB。
- **Axiom-Kolmogorov**：事件管理中心。以随机过程奠基人柯尔莫哥洛夫命名，承载告警接收、事件收敛、故障生命周期与事件关联分析。

平台整体遵循统一命名规范，所有子服务沿用 `Axiom-{数学家}` 范式，便于架构识别、服务治理与长期迭代扩展。
