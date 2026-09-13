// tie-dap / extension.js —— 最小 VS Code 调试扩展（p.9.2.3 DAP 客户端）
// 以 DebugAdapterExecutable 方式拉起 tie 自托管 DAP 适配器服务
// （compiler/dbug/tiedap.exe），在 stdin 上按 DAP 协议驱动 interp 执行器。
//
// 用法：
//   1. 构建 tiedap.exe（tiec compiler\dbug\tiedap.tie -o compiler\dbug\tiedap.exe）
//   2. 把本文件夹拷到 %USERPROFILE%\.vscode\extensions\tie-lang.tie-dap-0.1.0\
//      （或 VS Code 命令行 --install-extension 指向本目录），重启 VS Code
//   3. 在项目 .vscode/launch.json 用 type "tie" 配置（见 launch.json.example）
//   4. 打开目标 tie 源文件，F5 启动调试。
//
// 限制（运行至完成模型，见 docs/p.9.2.3.md）：支持 initialize / setBreakpoints /
// launch / configurationDone / threads / stackTrace / scopes / variables /
// continue / next / stepIn / stepOut / disconnect；line 断点命中于该行的首个
// 语句/函数入门事件；局部变量不可用（仅 Global 作用域，来自 interp 全局表）。

const vscode = require('vscode');

class TieDebugAdapterDescriptorFactory {
    createDebugAdapterDescriptor(session) {
        const program = vscode.Uri.joinPath(context.extensionUri, '..', '..', 'compiler', 'dbug', 'tiedap.exe');
        const exePath = program.fsPath;
        const cwd = session.workspaceFolder ? session.workspaceFolder.uri.fsPath : undefined;
        const exeOptions = { env: process.env, cwd: cwd };
        return new vscode.DebugAdapterExecutable(exePath, [], exeOptions);
    }
}
var context;

function activate(ctx) {
    context = ctx;
    context.subscriptions.push(
        vscode.debug.registerDebugAdapterDescriptorFactory('tie', new TieDebugAdapterDescriptorFactory())
    );
}
function deactivate() {}

module.exports = { activate, deactivate };