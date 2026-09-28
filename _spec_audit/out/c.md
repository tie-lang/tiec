## 第 6 章  数据结构

| 节 | 条目（规范要求） | 状态 | 证据 | 备注 |
| --- | --- | --- | --- | --- |
| 6.1 | struct 定义：字段含类型与默认值 | 已实现 | A: s6_1.exe 通过（Point{x,y,label} 规范版式）；B: pstmt_top.tie struct 解析 | — |
| 6.1 | 结构是纯数据、不含方法 | 已实现 | A: s6_6a 报 E00001「struct 体不允许方法定义」；B: diagcode_cat.gen.tie | — |
| 6.2 | 构造按字段顺序 + 点号字段访问 | 已实现 | A: s6_2.exe 通过（Point(1.0,2.0) / p.x=3.0 / p.label） | — |
| 6.2 | 结构作为参数默认按值传递 | 已实现 | A: s6_2b 打印 7 后 c.n 仍 0；s6_2c d.n=99 后 c.n 仍 0 | 但同名命名空间函数的接收者按引用传递（见 6.3），与「默认按值」口径不同 |
| 6.2 | 较大结构用只读借用/可写借用 | 未实现 | A: s6_3 报 E00000「参数 'p' 的 ref 修饰仅支持表参数（table/table<T>）或定长数组，实际是 Point」 | ROAD 359 明示「ref 扩展非表类型按设计属随后」，属已知未落地 |
| 6.3 | 命名空间函数第一参数即接收者 | 已实现 | A: s6_3b/s6_3d 通过（同名 ns 内改动回写：s6_3c c.n→5）；B: sinfer_p1.tie:580 | 非同名命名空间（util）内改动不回写（s6_3e c.n→0） |
| 6.3 | 规范示例 `pub func move_by(ref p: Point, dx, dy)` | 未实现 | A: s6_3 报 E00000（同上 ref 限制） | 规范用 ref 声明可写接收者，实现拒绝 |
| 6.4 | 点号调用转发 obj.method(args) = 同名 ns::method | 已实现 | A: s6_4.exe 通过（c.bump()/c.bump(step:4) 均正确）；B: sinfer_p1.tie:597 方法约定 | — |
| 6.4 | 方法的默认值参数 + 命名实参 | 已实现 | A: s6_4 通过（step 取默认 / step: 4）；B: ROAD 357 | — |
| 6.5 | 继承只复用字段（extends） | 已实现 | A: s6_5 通过（Circle("c",2.0)；c.name/c.r 可读） | — |
| 6.5 | 子类型可传给期望父类型的参数 | 未实现 | A: s6_5 报 E00377（var s: Shape = c）；s6_5b 报 E00588（take_shape(c)） | 规范称「子类型可以传给期望父类型的参数」不成立 |
| 6.6 | 结构体内不得定义函数 | 已实现 | A: s6_6a E00001 | — |
| 6.6 | 字段名跨继承链唯一 | 已实现 | A: s6_6b E00409「字段 'S.a' 与继承链中的字段重名」 | — |
| 6.6 | 继承链不得成环 | 已实现 | A: s6_6c E00209「struct 继承形成环」 | — |
| 6.6 | 字段默认值必须是常量表达式 | 未实现 | A: s6_6d 编译成功并运行（默认值含函数调用 side() 未被拒） | 该限制未在编译期检查 |
| 6.6 | 结构作参数不得隐式窄化 | 已实现 | A: s6_6e 报 E00588（f64 实参传 i64 形参） | — |
| 6.7 | 临时组合用元组（`var lo, hi = min_max(xs)`） | 部分实现 | A: s6_7 报 E00484「期望 '='，实际是 Comma」；s6_7b `var (a,b) = t` 通过 | 元组解构可用，但规范的逗号写法不可用，须带括号 |
| 6.8 | 运算符约定（按约定名函数接管 `+` `==` 等） | 部分实现 | A: 用规范名 s6_8 报 E00544、s6_8c 报 E00516；改用 op_add/op_eq s6_8d 通过（v.x=4、p==q 为 ne）；B: sinfer_p1.tie:581 | 约定名规范写错：实现为 op_add/op_sub/op_mul/op_div/op_mod/op_eq/op_ne/op_lt/op_le/op_gt/op_ge/op_neg（ROAD 134）；规范列出的 index/index_set/cmp/to_string 无对应实现 |
| 6.9 | 计算属性读（`c.area` 触发同名函数） | 已实现 | A: s6_9b 通过（area/label 读为计算值） | — |
| 6.9 | 计算属性写（`attr_set`） | 已实现 | A: s6_9c c.label_set("x") 回写 tag；只读属性写报 E00551（s6_9d）；B: ROAD 137 | 规范写的 `label_set(ref c: Circle, v: string)` ref 形参被拒（同 6.2） |
| 6.10 | 遍历约定（has_next/next 名下函数，for 可消费） | 已实现 | A: s6_10b 通过（for v in ring 打印 10 20 30）；B: ROAD 346 | — |

> 本章：已实现 15 / 部分实现 2 / 未实现 4 / 非规范条目 0

## 第 7 章  接口

| 节 | 条目（规范要求） | 状态 | 证据 | 备注 |
| --- | --- | --- | --- | --- |
| 7.1 | port 声明方法签名集合 | 已实现 | A: s7_2.exe 通过；B: pstmt_top.tie:198 | — |
| 7.1 | self 为接收者占位 | 已实现 | A: s7_2（impl 体 self.label 可访问字段） | — |
| 7.2 | `impl Drawable for Button` 逐方法给出实现 | 已实现 | A: s7_2 通过；B: scollect_port_p1.tie:226 | — |
| 7.2 | 遗漏方法在编译期报告 | 已实现 | A: s7_2b 报 E00210「impl 'Drawable for B' 缺少方法 'bounds'」 | — |
| 7.3 | 泛型参数可标注接口约束（静态分派） | 已实现 | A: s7_6 通过（<T: Named> 静态绑定）；B: tests/s24_probe/probe1_static.tie | — |
| 7.3 | 约束不满足报错 | 已实现 | A: s7_3b 报 E00556「类型 'NoImpl' 未实现 port 'Drawable'」 | — |
| 7.3 | 规范示例形参 `items: table<T>` | 未实现 | A: s7_3「IR 生成失败: 行池 table<R> 不能作函数形参」 | 泛型约束本身可用，但规范给的 table<T> 形参形态后端不支持（ROAD 388 记 v1 拒绝返回值/形参行池） |
| 7.4 | 接口作为运行期对象（动态派发） | 部分实现 | A: s7_4b 通过（unsafe{ var d: Drawable = b } + table<Drawable>=[d,d2]，打印 Button(ok)/Label(hi)）；s7_4c 报 E00489 table_new_Drawable 未定义；s7_4 报 E00377（异质字面量入表推为 table<any>） | 需 unsafe 提升 + 先提升为接口对象再入表；规范的 `table_new_Drawable()` 不存在 |
| 7.5 | 接口可以要求另一个接口（组合） | 非规范条目 | A/B 无对应语法：grep compiler/ 无 requires / port 继承语法；规范示例仅并列声明两个 port | 规范未给出「要求」的表达语法，无可判定特性 |
| 7.6 | 名义接口（port + impl，须显式声明） | 已实现 | A: s7_2 通过 | — |
| 7.6 | 结构接口 `interface`（具备方法即满足） | 已实现 | A: s7_6 通过（Circle 无 impl 即满足 Named）；B: lex_tokdefs.tie:135（tag106）、tests/language/interface_trait.tie | — |
| 7.6 | interface 亦可作泛型约束 | 已实现 | A: s7_6（<T: Named> 消费 interface） | — |

> 本章：已实现 9 / 部分实现 1 / 未实现 1 / 非规范条目 1

## 第 8 章  错误处理

| 节 | 条目（规范要求） | 状态 | 证据 | 备注 |
| --- | --- | --- | --- | --- |
| 8.1 | 语言提供两个通用型别（有值/无值、成功/错误） | 已实现 | A: import "…/lib_v1/std/result.tie" 后 s8_1a2 通过 | 非内建：Option/Result 是 std/result.tie 里的预置 enum，须显式 import；无 prelude 自动注入 |
| 8.1 | 规范示例 `to_int(s)` | 未实现 | A: s8_2e 报 E00489「未定义的函数 'to_int'」 | 实现名为 parse_int |
| 8.1 | switch 解构 Some/None、Ok/Err | 已实现 | A: s8_1a2、s8_1b 通过 | — |
| 8.2 | `?` 传播（Err/None 提前返回） | 已实现 | A: s8_2c 通过（div(10,2)? → 输出 6） | — |
| 8.2 | 规范示例 `cfg["port"]?` | 未实现 | A: s8_2d 报 E00223「'?' 解包的操作数必须是 Result/Option 枚举，实际是 string」 | 映射下标返回元素类型而非 Option，规范假设不成立 |
| 8.3 | switch 多分支展开结果类型 | 已实现 | A: s8_1b 通过（case Ok(v)/Err(msg)） | — |
| 8.3 | `?:` 安全默认值 | 已实现 | A: s8_3c2 通过（Option.Some(5) ?: 8080 → 5）；B: sinfer_ie_ie1.tie:692 | 要求左侧 Option<T>；规范示例 `cfg["port"] ?: 8080` 不成立（映射下标非 Option） |
| 8.4 | 标准组合子 `-> map_result(...)` / `-> and_then(...)` | 未实现 | A: s8_4 报 E00489「未定义的函数 'map_result'」；lib_v1/std/result.tie 仅含两个 enum，全仓无 map_result/and_then | std 未提供任何 Result/Option 组合子（测试里的 r_map 等均为用户自定义） |
| 8.5 | panic 终止并携带消息 | 已实现 | A: s8_5.exe 打印消息、rc=1 | — |
| 8.5 | 可捕获 panic 转普通错误 | 已实现 | A: s8_5e catch_panic 捕获深层 panic（打印 boom/caught）；B: sbuiltin_q1.tie:61 | 规范未给语法；实现为内建 catch_panic(f) -> bool |
| 8.5 | 数组越界内建检查、不可关闭 | 部分实现 | A: s8_5b（table 越界读→0、rc=0）；s8_5c（array<i64,3> 越界→段错误 rc=139）；加 `--check-bounds` 后 s8_5c_cb 报「array index out of bounds: index 5, len 3」rc=1 | 检查默认关、须显式 --check-bounds，与规范「不可关闭」相反；ROAD 384 明示「越界读语义不动」 |
| 8.5 | 除零触发内建检查 | 未实现 | A: s8_5d 除零→硬崩溃（默认与 --check-bounds 均无诊断消息） | — |
| 8.5 | 带检查运算的溢出检查 | 已实现 | A: s8_5f `a +? 1` → 打印 "checked add overflow" rc=1 | — |
| 8.6 | 错误值应携带上下文（可枚举用枚举/否则文本） | 非规范条目 | A: Result.Err(string) 可用（s8_1b） | 属错误值内容约定，无独立可编译语言特性 |

> 本章：已实现 8 / 部分实现 1 / 未实现 4 / 非规范条目 1

## 第 9 章  模块与导入

| 节 | 条目（规范要求） | 状态 | 证据 | 备注 |
| --- | --- | --- | --- | --- |
| 9.1 | `import "./x.tie" as geo` 别名限定访问 | 已实现 | A: ch09/s9_1 通过（geo.distance(9,4)=5） | — |
| 9.1 | `import "./x.tie"` 无别名，公开名进入作用域 | 已实现 | A: s9_1 通过（fmt_it(7) 裸调） | — |
| 9.2 | 命名空间跨文件合并 | 已实现 | A: s9_2 通过（主文件 math.gcd + 分片 math.lcm 均可用） | — |
| 9.2 | 命名空间可嵌套 | 已实现 | A: ch09/s9_2b 通过（outer.inner.f()=11） | — |
| 9.3 | 声明默认私有，仅 pub 对外可见 | 部分实现 | A: s9_3c 报 E00332（ns 内非 pub `lib::secret` 跨文件不可调用）；s9_3b 文件顶层非 pub `helper()` 被导入方裸调成功 | 命名空间内可见性受检；文件顶层（无 ns）可见性未强制 |
| 9.4 | 标准库模块清单（14 个） | 已实现 | A: string/utf/collection/sort/math/regex/fs/path/json/time/random/process/net/crypto 逐个 `import "/std/<m>.tie"` 编译通过；实际 ~34 模块 | 规范表所列 14 个全部存在；实现另含 result/version/csv/db/graph 等未列模块 |
| 9.5 | 包管理器按版本解析依赖、版本范围记号 | 部分实现 | B: tpkg/main.tie、tie.pkg、lib_v1/std/version.tie:52 satisfies（支持 `*` / `^x.y` / `>=x.y` / 精确版本）；fetch.tie:306 is_constraint | 规范的 `~1.4`（波浪号）记号未实现；`^`/`>=` 可用 |
| 9.6 | 选择性导入 `import "p.tie".{ a, b }` | 已实现 | A: ch09/s9_6a 通过；B: semantic_p1.tie:344（p.9.11.31） | — |
| 9.6 | 重导出 `pub import` | 已实现 | A: s9_6d 通过（reexp.tie pub import format.tie → 导入方见 fmt_it） | — |
| 9.6 | 规范路径写法 `import "std/string"` | 未实现 | A: s9_6b 报 E00483「无法读取导入文件 'std/string'（文件不存在）」 | 实现须写 `/std/string.tie`（s9_6c 通过）；规范省略扩展名与前导斜杠 |
| 9.7 | `using` 把命名空间名字引入当前作用域 | 已实现 | A: s9_7 通过（using geo; → distance 裸调）；s9_7c 通过（using outer.inner; → g() 裸调） | 点式与带分号形态均可用 |
| 9.8 | 数据格式：文本 td 与等价二进制 zd 互转 | 已实现 | A: `tiec.exe --compress-data data/api.data.tie -o data/api.zd` 成功产出 214B zd；B: cli_args.tie:35 | 文本形式即表字面量（`type tie<data>`） |
| 9.9 | 依赖声明：项目文件含名称与版本范围 | 部分实现 | B: dist-release/stage/win/examples/demo_pkg/tie.pkg（`"dependencies": [ "lib_colors": "path:…", "log": "1.0.0" ]`）+ version.satisfies | 规范的 `require: json ^2.1` 行式写法与实现 tie.pkg 表字面量格式不同；`~` 未支持 |

> 本章：已实现 9 / 部分实现 3 / 未实现 1 / 非规范条目 0

## 记录更正

本路（ch06–ch09）实测未发现 ROAD.md 记录与实现不符的条目，无需更正记录。相关记录经复核均与实测一致：

- ROAD.md 第 134 行 `[x]` 运算符重载 —— 实测 op_add/op_eq 可用（s6_8d），记录属实；偏差在规范侧（§6.8 约定名写成 add/eq）。
- ROAD.md 第 137 行 `[x]` 计算属性 —— 实测 getter/setter/只读写诊断均成立（s6_9b/s6_9c/s6_9d），记录属实。
- ROAD.md 第 346 行 `[x]` 迭代器协议 has_next/next —— 实测通过（s6_10b），记录属实。
- ROAD.md 第 351 行 `[x]` interface 结构性接口 —— 实测通过（s7_6），记录属实。
- ROAD.md 第 359 行 ref 扩展非表类型属「随后」 —— 与实测 E00000 一致（s6_3），记录属实。
- ROAD.md 第 365 行 `[x]` 选择性导入 —— 实测通过（s9_6a/s9_6d），记录属实。
- ROAD.md 第 384 行 越界读语义不动 —— 与实测一致（s8_5b 越界读→0），记录属实。
- ROAD.md 第 210 行 `[x]` 包管理器版本约束 x.y.z·^·>=·* —— 与实测一致（无 `~`），记录属实；偏差在规范侧（§9.5/§9.9 用了 `~`）。
- ROAD.md 第 556 行 `[x]` II1 可见性（限定「namespace 内」）—— 与实测一致（E00332）；规范 §9.3 把该规则扩到文件顶层，属规范侧越界表述。

## 本路结论

1. **最严重（规范示例不可编译，且属真未实现）**：
   - §6.8 运算符约定名整表写错——规范用 `add/sub/eq/cmp/index/to_string`，实测 E00544/E00516；实现名是 `op_add/op_eq/...`（s6_8 vs s6_8d）。规范与实现冲突，不是未实现。
   - §8.4 `map_result` / `and_then` 组合子完全不存在（E00489），std/result.tie 只定义了两个 enum；全仓无任何 Result/Option 组合子。
   - §8.5「数组越界/除零触发内建检查且不可关闭」不成立：默认无检查（越界读→0、定长越界段错误、除零段错误），越界检查须显式 `--check-bounds` 且默认关。
   - §6.5「子类型可传给期望父类型的参数」不成立（E00377/E00588），只有字段继承可用。
   - §6.2/§6.3 规范用 `ref p: Point` 声明可写借用——实现明确拒绝（E00000，仅支持表/定长数组），ROAD 359 记为已知后置项。
2. **规范与实现冲突（实现有、规范写得不对）**：
   - §6.8 约定名（见上）；§9.6 导入路径 `import "std/string"` 须写 `/std/string.tie`（E00483）；§8.1 转换函数名 `to_int` 实现为 `parse_int`；§9.5/§9.9 版本记号 `~1.4` 未实现（仅 `^`/`>=`/`*`）；§8.2 `cfg["port"]?` 不成立（映射下标非 Option）。
3. **部分实现要留意**：§7.3 泛型约束可用但规范的 `table<T>` 形参后端拒绝（IR 生成失败）；§7.4 接口对象动态派发可用但须 unsafe 提升且 `table_new_Drawable()` 不存在；§6.7 元组解构须带括号（`var (a,b)=`）而非规范的逗号写法；§9.3 命名空间内可见性受检、文件顶层未强制。
4. **已确证可用的核心机制**（供合并参考）：struct 定义/构造/字段访问/点号方法转发/默认值+命名实参、extends 字段继承、接口 port+impl+缺方法诊断、interface 结构性接口、泛型约束、Option/Result（import 后）+ `?` 传播 + `?:` + switch 解构、panic + catch_panic、checked 运算（`+?` 等）、命名空间跨文件合并与嵌套、别名/无别名/选择性导入/`pub import`/`using`、14 个标准库模块、td→zd 数据格式。
5. **规范缺口（实现有、规范未写）**：接口对象提升须在 `unsafe` 块内（规范 §7.4 未提）；捕获 panic 的内建名 `catch_panic` 与 `try {}` 块（规范 §8.5 只说「可以捕获」未给语法）；越界检查开关 `--check-bounds`（规范 §8.5 反而称「不可关闭」）。
6. **附带发现**：`port` 是保留关键字，规范 §8.1/§8.2/§8.3 多处用 `var port = …` 作变量名——实测报 E00485「期望标识符」（改名后即通过），规范示例本身不可编译。
