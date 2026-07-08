# 如何构建一个 RL 环境（逐句翻译 baseline）

Andrej Karpathy 用三个名词总结了 LLM 训练的整个历史：文本、对话、环境。

预训练跑在互联网文本上，监督微调跑在精心策划的对话上，而当前的强化学习时代跑在环境上。

OpenAI 的 o1 通过在有可验证答案的数学和编程问题上训练证明了这个框架，DeepSeek-R1 则公开发布了这套配方。

整个行业现在把环境当作稀缺资源。据报道 Anthropic 曾讨论一年内花超过 10 亿美元在环境上。

与此同时，有人在通过一个类似 Hugging Face 的中心免费提供 2500 多个开源环境。

今天，我们要用他们的框架从零构建一个自己的环境。

## 理解 RL 环境的四个组成部分

在构建任何东西之前，先理解环境到底是什么。每个 RL 设置都是一个包含四个运动部分的循环，它们映射到模型交互的任何事物：

- State（状态）：模型当前看到的内容
- Action（动作）：它从该状态做出的选择
- Reward（奖励）：一个表示这个选择有多好的数字
- Environment（环境）：持有状态、接受动作、返回奖励的东西

这个循环中最难的部分一直是奖励，传统上需要在人类偏好数据上训练一个单独的模型。

DeepSeek-R1 通过 GRPO（Group Relative Policy Optimization，组相对策略优化）用一个普通的 Python 函数替代了整个奖励模型。对同一个提示的多个答案打分，然后把模型推向那些超过组平均值的答案。

## 环境是最后的壁垒

这样奖励模型这个障碍就被拆掉了，剩下的壁垒就是环境本身。奖励函数可以对最终状态打分，但必须有东西来呈现任务、接受模型的动作、执行规则，并首先生成那个最终状态。

前沿实验室把这部分当作专有资产严密保护，这就是为什么很少有从业者见过一个真正的环境从内部是什么样子。

免费提供环境的团队是 Prime Intellect，他们的库叫 Verifiers，就是我们要用的框架（100% 开源）。

设计是与模型无关的（model-agnostic），奖励是完全可验证的，同一套骨架适用于你想训练的任何回合制任务。

## 如何读这篇文章

目标很简单。我们要构建一个完整的 RL 环境，即使这是你的第一次，我们也会用一种容易消化的方式讲解。

每个想法都伴随着实现它的代码，代码短到可以在文章的流动中阅读。完整的、可运行的版本在最后分享。

我们围绕的这个游戏只是一个工作示例。当你读完时，你能够拿这个完全相同的结构去适配你自己的用例。

## Othello RL 环境：为什么选一个棋盘游戏

Othello（黑白棋）是在 8x8 网格上进行的双人游戏。你放置一个棋子，让它在直线上夹住对手的棋子，每一个被夹住的棋子都翻转为你的颜色，谁在棋盘填满时拥有更多棋子谁就赢。

那个翻转规则就是为什么单次移动可以大幅改变分数，也是为什么角落如此重要（一个角落棋子永远不能被翻回来）。

每一个 RL 部分在这里都有归属。棋盘是 State，落子是 Action，最终结果喂给 Reward，验证走法、翻转棋子、扮演另一方的游戏引擎是 Environment。

LLM 执黑，内置引擎执白。每次黑棋落子后，白棋回应，更新的棋盘回到模型，如此重复直到游戏结束。

## 技术栈

三个工具让这一切工作起来，每个处理一层：

- Verifiers：RL 框架。它定义环境、运行回合循环、处理评估。
- Lightning AI：一个 OpenAI 兼容的推理 API，所以同样的代码可以调用 Claude 或 DeepSeek 这些托管模型，无需针对特定提供商重写。
- vLLM：在同一个 OpenAI 兼容端点后本地服务开源权重模型。

共享的接口就是让环境与模型无关的原因。本地的 Ministral-3B 和托管的 GPT-4.1 可以一行切换：你只改模型名，其他什么都不变。

## 游戏循环

这是模型在每个回合看到的：棋盘、分数、有效走法列表就是全部状态。模型对游戏的所有认知都来自这段文本。

它必须以一个 `<think>` 部分回应，后跟一个 `<move>` 标签，这迫使它在提交走法之前对局面进行推理。

环境根据有效走法列表验证移动，将其应用到棋盘上，让白棋回应，然后把更新的棋盘发回。无效走法收到错误信息和重试机会，并对奖励施加惩罚。

所有这些都在一个方法里。OthelloEnv 继承自 Verifiers 中的 MultiTurnEnv，后者处理循环、回合追踪和终止，基类每次模型发送一步走法时都调用你的 env_response：

```python
class OthelloEnv(MultiTurnEnv):
    def env_response(self, model_output, state):
        move = parse_move(model_output)
        if not is_valid(move, state.board):
            state.penalty += INVALID_MOVE_PENALTY
            return error_message(move), state
        state.board = apply_move(state.board, move, player="black")
        if not game_over(state.board):
            white_move = opponent_engine(state.board, state.difficulty)
            state.board = apply_move(state.board, white_move, player="white")
        return render_board(state.board), state
```

这是逻辑的形状；真实版本还处理片段跳过的棋盘解析和边缘情况。我稍后会分享完整可运行的代码，一旦我们理解了端到端的设置。

## 内置对手引擎

内置引擎执白，有两种模式：

Random（随机）：任选合法走法。对早期训练有用，因为模型只要做出合理决定就能获胜。

Minimax（极小化极大）：模拟未来走法，用角落控制、棋盘位置、可用走法给每个结果局面打分，选择最坏情况结果最好的走法。深度 3 意味着它向前看三步，足以设陷阱、避免明显失误。

一个随机性参数控制白棋多长时间忽略其策略而随机选择。更低的随机性意味着更一致、更惩罚性的对弈。

白棋的走法根据当前棋盘状态和固定的游戏种子生成，所以同一个局面总是产生同一个响应。这种确定性就是允许你在相同条件下比较不同模型的原因。

```python
def opponent_engine(board, randomness, depth):
    if random.random() < randomness:
        return random.choice(legal_moves(board))
    best_move = None
    best_score = float("-inf")
    for move in legal_moves(board):
        score = minimax(apply_move(board, move), depth - 1, my_turn=False)
        if score > best_score:
            best_move, best_score = move, score
    return best_move
```

## 奖励函数

游戏结束时，四个信号合并成一个奖励。每一个都是一个函数，从最终状态读取某些东西，返回一个数字。胜利信号是最简单的：

```python
def win_reward_func(state):
    result = state.get("result")
    if result == "black":
        return 1.0
    if result == "draw":
        return 0.5
    return 0.0
```

其他三个遵循相同的形状，四个组合成一个分数：

```python
def total_reward(state):
    return (
        win_loss_score(state)
        + piece_advantage(state)
        + format_compliance(state)
        - invalid_move_penalty(state)
    )
```

用四个信号而不是单一胜负位的原因是分辨率。训练早期大多数比赛都是失败，对纯胜负奖励它们看起来都相同，所以模型没有攀登的方向。

棋子优势（piece_advantage）把接近的失败和大败区分开，在模型开始获胜之前给它梯度。

格式合规（format_compliance）权重低，所以干净的格式永远不会盖过好的对弈。

无效走法惩罚被封顶，所以一个坏局不能淹没模型做对的一切。

每个分数直接来自游戏状态和规则，没有裁判模型或 LLM 评估器参与，所以奖励是完全确定性和可复现的。

## 连接起来

环境跨不同的起始位置和对手难度生成游戏，模型通过上面的循环玩每一个，游戏结束时四个奖励被计算并合并。评估期间，奖励、token 使用和回合数在所有游戏中汇总到一个结果表中。

一个函数把所有东西连接起来，这就是 prime eval 命令在后台调用的东西：

```python
def load_environment(min_random_move_prob, max_random_move_prob, parse_think):
    dataset = generate_games(min_random_move_prob, max_random_move_prob)
    parser = XMLParser(fields=["think", "move"])
    rubric = Rubric(funcs=[...], weights=[1.0, 1.0, 0.2, 1.0])
    return OthelloEnv(dataset, parser, rubric)
```

## 数字告诉我们什么

运行一次评估是一条命令，把对手设置作为参数传入：

```bash
prime eval run othello -m openai/gpt-4.1 -n 100 \
  -a '{"min_random_move_prob": 0.0, "max_random_move_prob": 0.0, "minimax_depth": 3}'
```

换一个模型名字来测试别的，无论它是通过 Lightning AI 托管的还是运行在本地 vLLM 服务器上。

## 从评估到训练

评估告诉你模型在哪里挣扎，训练分三个阶段来修复。同一个环境支持所有阶段：

数据生成：让你最强的模型玩几百局并保存结果。同一个 eval 命令直接写入数据集：

```bash
prime eval run othello -m openai/gpt-4.1 -n 200 \
  --save-to-hf-hub --hf-hub-dataset-name your-username/othello-data
```

在训练之前把它筛选到只剩获胜和平局，这样你就不会教模型和你最强对手的格式一起犯它的错误。

监督微调：先教格式和有效走法。Ministral-3B 的回合计数直接说明了这一点，因为不可靠的格式和非法走法是 RL 无法训练穿透的噪声。

RL 训练：这是策略改进的地方。从同一个起始位置玩多局，每局用评估中相同的奖励函数打分，模型被更新朝向得分更高的 rollout。

剥离到核心，这就是文章顶部的 GRPO 循环：

```python
for prompt in batch:
    rollouts = [play_game(model, prompt) for _ in range(group_size)]
    rewards = [total_reward(r.final_state) for r in rollouts]
    advantage = rewards - mean(rewards)
    update_model(model, rollouts, advantage)
```

每个 rollout 都被打分与其自己组的平均值比较，所以从给定位置赢 10 场中 6 场的走法比它旁边较弱的尝试得到更多奖励。

## 适配到你自己的任务

一旦你去掉 Othello 特定的东西，同一个 MultiTurnEnv 给你一个适合任何回合制任务的骨架：

```python
class TaskEnv(MultiTurnEnv):
    def env_response(self, model_output, state):
        action = parse_action(model_output)
        if not is_valid(action, state):
            return error_message(action), penalize(state)
        state = apply_action(state, action)
        if not task_complete(state):
            state = environment_step(state)
        return render_state(state), state
```

这不是游戏专用的。一个编码 Agent 把 apply_action 换成对生成的代码运行测试套件，一个客服 Agent 换成检查工具调用是否检索了正确的记录，一个研究任务换成对照引用的来源验证声明。

适配它归结为四个替换：

- 任务逻辑：你领域的规则，什么算有效动作，状态如何变化
- 响应引擎：模型对什么做出反应，从基于规则的模拟器到实时 API 到另一个模型
- 奖励函数：保留模式（结果信号、部分学分、格式、惩罚），替换领域逻辑
- 状态渲染：模型需要看到什么，无论是文件 diff、对话记录还是工具的响应

底层的结构在不同领域都保持相同：解析、验证、应用、响应、打分。评分标准（rubric）就是设计，如果你把组件搞对了，训练信号会照顾好自己。

## 试试看

所有代码、设置说明和现成可用的 GPU 都在 Lightning AI Studio 模板中，用于复现这些结果。
