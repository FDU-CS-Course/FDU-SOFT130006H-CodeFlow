这个仓库fork自deerflow。

deer-flow原本是一个开源的Deep Research Flow，我们希望复用它的Workflow框架，更换工具组合，来实现一个AI-based缺陷分析-误报检测工具。

## 需求

- 输入File, Line, Severity, Id, Summary （来自传统缺陷分析工具CppCheck的输出）
- 跳过Coordinator，直接从Planner开始
- Planner的输入：
  - CppCheck的输出
  - `File`文件中的内容（Line前后若干行）
  - 待检测项目的目录树
- 正常调用Research Team和Reporter
- Reporter在输出Markdown格式的报告之后，在结尾附上一个简短的json格式总结

```json
{
  "defect_type": str, # false_positive, style, perf, bug
  "defect_description": str
}
```

## 工具组合

- “代码库搜索”，在给定范围查找某个关键词（函数、类、变量），返回每个出现的位置和前后内容
- “文件阅读”，在给定范围读取文件内容
- “代码库模糊搜索”，在整个仓库模糊检索（使用Embedding模型和向量召回），返回每个出现的位置和前后内容
