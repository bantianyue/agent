# -*- coding: utf-8 -*-
# 表格真相源：逐单元格取自源页面 <table>，数字与配置字符串原样保留。

G = 'color:#1a7f5a;'      # 优势项
O = 'color:#c2610a;'      # 劣势项


def b(text, color=None):
    style = 'color:%s;font-weight:600;' % color if color else 'color:#0F4C81;font-weight:600;'
    return '<strong style="%s">%s</strong>' % (style, text)


TABLES = {
    # 双后缀树缓存
    't0': {
        'head': ['树类型', '模式来源', '在推测中的作用'],
        'rows': [
            [b('本地树（Per-Request）'),
             '当前请求的提示词，以及该请求内已经生成的 token',
             '捕获同一个会话内部的即时自我重复模式'],
            [b('全局树'),
             'vLLM 服务此前处理过的所有请求的输出',
             '提供对常见 LLM 输出的深层统计知识，是智能体重复场景的关键'],
        ],
    },
    # 8B 四种实验配置
    't1': {
        'head': ['技术', '目标模型', '推测配置'],
        'rows': [
            ['基线（不做推测）', 'Llama-3.1-8B-Instruct', '无（标准自回归）'],
            ['N-Gram Matching', 'Llama-3.1-8B-Instruct', '{"method": "ngram", "prompt_lookup_max": 4}'],
            ['Suffix Decoding', 'Llama-3.1-8B-Instruct', '{"method": "suffix"}'],
            ['EAGLE', 'Llama-3.1-8B-Instruct',
             '{"method":"eagle", "model":"yuhuili/EAGLE-LLaMA3.1-Instruct-8B", "draft_tensor_parallel_size":1, "num_speculative_tokens":2}'],
            ['EAGLE 3', 'Llama-3.1-8B-Instruct',
             '{"method":"eagle3", "model":"yuhuili/EAGLE3-LLaMA3.1-Instruct-8B", "draft_tensor_parallel_size":1, "num_speculative_tokens":2}'],
        ],
    },
    # 70B 四种实验配置
    't2': {
        'head': ['技术', '目标模型', '推测配置'],
        'rows': [
            ['基线（不做推测）', 'Llama-3.3-70B-Instruct', '无（标准自回归）'],
            ['N-Gram Matching', 'Llama-3.3-70B-Instruct', '{"method": "ngram", "prompt_lookup_max": 4}'],
            ['Suffix Decoding', 'Llama-3.3-70B-Instruct', '{"method": "suffix"}'],
            ['EAGLE', 'Llama-3.3-70B-Instruct',
             '{"method":"eagle", "model":"RedHatAI/Llama-3.3-70B-Instruct-speculator.eagle3", "draft_tensor_parallel_size":1, "num_speculative_tokens":2}'],
            ['EAGLE 3', 'Llama-3.3-70B-Instruct',
             '{"method":"eagle3", "model":"RedHatAI/Llama-3.3-70B-Instruct-speculator.eagle3", "draft_tensor_parallel_size":1, "num_speculative_tokens":2}'],
        ],
    },
    # speculative-config 字符串
    't3': {
        'head': ['技术', '配置字符串'],
        'rows': [
            ['基线', '--speculative-config（直接去掉该参数）'],
            ['N-Gram', '{"method": "ngram", "num_speculative_tokens": 5, "prompt_lookup_max": 4}'],
            ['Suffix', '{"method": "suffix"}'],
            ['EAGLE', '{"method": "eagle", "model": "yuhuili/EAGLE-LLaMA3.1-Instruct-8B", "num_speculative_tokens": 2, "draft_tensor_parallel_size": 1}'],
            ['EAGLE 3', '{"method": "eagle3", "model": "yuhuili/EAGLE3-LLaMA3.1-Instruct-8B", "num_speculative_tokens": 2, "draft_tensor_parallel_size": 1}'],
        ],
    },
    # 8B / ShareGPT
    't4': {
        'head': ['解码方法', '输出吞吐（tok/s）', '平均每 token 耗时（ms）', '平均 token 间延迟（ms）', '相对基线加速'],
        'rows': [
            ['N-gram Matching', '491', '21.85', '24.8', '1.17x'],
            ['Suffix Decoding', '585', '18.21', '26.1', '1.39x'],
            ['EAGLE-3', '589', '17.90', '29.2', '1.40x'],
            [b('EAGLE（最佳）', '#1a7f5a'), b('601', '#1a7f5a'), b('17.49', '#1a7f5a'), b('31.1', '#1a7f5a'), b('1.43x', '#1a7f5a')],
        ],
    },
    # 8B / SWE-bench Lite
    't5': {
        'head': ['解码方法', '输出吞吐（tok/s）', '平均每 token 耗时（ms）', '平均 token 间延迟（ms）', '相对基线加速'],
        'rows': [
            ['N-gram Matching', '406', '23.90', '28.4', '1.10x'],
            ['EAGLE', '398', '24.40', '30.0', '1.08x'],
            ['EAGLE-3', '379', '25.56', '29.5', '1.03x'],
            [b('Suffix Decoding（最佳）', '#1a7f5a'), b('534', '#1a7f5a'), b('18.10', '#1a7f5a'), b('31.8', '#1a7f5a'), b('1.45x', '#1a7f5a')],
        ],
    },
    # 70B / ShareGPT
    't6': {
        'head': ['解码方法', '输出吞吐（tok/s）', '平均每 token 耗时（ms）', '平均 token 间延迟（ms）', '相对基线加速'],
        'rows': [
            ['EAGLE（标准）', '351', '22.81', '24.8', '1.02x'],
            ['N-gram Matching', '385', '21.90', '23.7', '1.12x'],
            ['Suffix Decoding', '455', '18.24', '24.8', '1.33x'],
            [b('EAGLE-3（最佳）', '#1a7f5a'), b('537', '#1a7f5a'), b('15.95', '#1a7f5a'), b('25.5', '#1a7f5a'), b('1.57x', '#1a7f5a')],
        ],
    },
    # 70B / SWE-bench Lite
    't7': {
        'head': ['解码方法', '输出吞吐（tok/s）', '平均每 token 耗时（ms）', '平均 token 间延迟（ms）', '相对基线加速'],
        'rows': [
            ['EAGLE（标准）', '377', '25.38', '28.4', '1.01x'],
            ['N-gram Matching', '416', '23.20', '27.0', '1.11x'],
            ['Suffix Decoding', '522', '18.32', '30.6', '1.39x'],
            [b('EAGLE-3（最佳）', '#1a7f5a'), b('601', '#1a7f5a'), b('15.73', '#1a7f5a'), b('32.1', '#1a7f5a'), b('1.60x', '#1a7f5a')],
        ],
    },
    # 选型建议
    't8': {
        'head': ['使用场景', '推荐方法', '在测试中表现好的原因'],
        'rows': [
            ['通用聊天机器人（客服、角色扮演）', b('EAGLE / EAGLE-3'),
             '训练过的草稿头更擅长预测人类对话里流动且不可预测的内容'],
            ['编码助手（小模型）', b('Suffix Decoding'),
             '对计算受限的小模型，低开销的启发式匹配效果最好：Suffix Decoding 利用代码重复性，又不引入草稿模型开销'],
            ['代码与智能体（大模型）', b('EAGLE-3'),
             '在显存受限的 70B 上，EAGLE-3 的高准确率减少了昂贵的权重访问，表现甚至超过模式匹配方法'],
            ['硬件受限（显存紧张）', b('Suffix Decoding'),
             '不需要额外权重、也不需要训练，在显存紧张时是一份免费的加速'],
        ],
    },
}
