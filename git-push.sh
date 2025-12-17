#!/bin/bash

# 检查是否提供了提交信息
if [ $# -eq 0 ]; then
    echo "请提供提交信息作为参数，例如: $0 '修复了登录bug'"
    exit 1
fi

commit_message="$*"

# 执行 git add . 添加所有变更文件
echo "执行 git add . ..."
git add .

# 检查 add 命令是否成功执行
if [ $? -ne 0 ]; then
    echo "git add 执行失败"
    exit 1
fi

# 执行 git commit
echo "执行 git commit ..."
git commit -m "$commit_message"

# 检查 commit 命令是否成功执行
if [ $? -ne 0 ]; then
    echo "git commit 执行失败"
    exit 1
fi

# 执行 git push
echo "执行 git push ..."
git push

# 检查 push 命令是否成功执行
if [ $? -ne 0 ]; then
    echo "git push 执行失败"
    exit 1
fi

echo "所有操作执行完成！"

# 运行命令
# git pull origin main
# ./git-push.sh "更新了html2image_toolkit，加入了streamlit 前端"

# streamlit run portal.py