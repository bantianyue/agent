# 全文逐句翻译（baseline）

State：模型当前看到的局面。
Action：它基于该状态做出的选择。
Reward：一个说明这个选择有多好的数字。
Environment：那个持有状态、接收动作、并返回奖励的东西。

How to read this article（如何阅读本文）
The Othello RL env：Why a board game（奥赛罗 RL 环境：为什么选一个棋盘游戏）

Tech stack（技术栈）
Verifiers：RL 框架。它定义环境、运行回合循环、并处理评估。
Lightning AI：一个 OpenAI 兼容的推理 API，所以同一份代码可以调用 Claude 或 DeepSeek 这类托管模型，而不需要针对特定供应商重写。
vLLM：在同样的 OpenAI 兼容端点后面，于本地提供开放权重模型。

The game loop（游戏循环）
class OthelloEnv(MultiTurnEnv):
    def env_response(self, model_output, state):
        move = parse_move(model_output)
        if not is_valid(move, state.board):
            state.penalty += INVALID_MOVE_PENALTY
            return error_message(move), state          # 同一回合，重试
        state.board = apply_move(state.board, move, player="black")
        if not game_over(state.board):
            white_move = opponent_engine(state.board, state.difficulty)
            state.board = apply_move(state.board, white_move, player="white")
        return render_board(state.board), state

The built-in opponent engine（内置的对手引擎）
Random picks any legal move. Useful for early training, since the model can win just by making reasonable decisions.（随机：选择任意合法走法。在训练早期很有用，因为模型只要做出合理的决策就能赢。）
Minimax simulates future moves, scores each resulting position by corner control, board position, and available moves, and picks the move with the best worst-case outcome. Depth-3 means it looks three moves ahead, enough to set traps and avoid obvious blunders.（极小化极大算法模拟未来的走法，依据角点控制、棋盘位置和可用走法对每个结果局面打分，并选出最坏情况下结果最好的那一步。Depth-3 意味着它向前看三步，足以设下陷阱并避免明显的失误。）

def opponent_engine(board, randomness, depth):
    if random.random() < randomness:               # random mode
        return random.choice(legal_moves(board))
    best_move = None                                 # minimax mode: try every move,
    best_score = float("-inf")                       # keep the one with the best score
    for move in legal_moves(board):
        score = minimax(apply_move(board, move), depth - 1, my_turn=False)
        if score > best_score:
            best_move, best_score = move, score
    return best_move

The reward functions（奖励函数）
def win_reward_func(state):
    result = state.get("result")
    if result == "black":   # the model's color
        return 1.0
    if result == "draw":
        return 0.5
    return 0.0              # loss, or game never finished

def total_reward(state):
    return (
        win_loss_score(state)
        + piece_advantage(state)
        + format_compliance(state)
        - invalid_move_penalty(state)
    )

Piece advantage separates a close loss from a blowout, giving the model gradient before it starts winning.（棋子优势能把一场惜败和一场溃败区分开，让模型在它开始赢棋之前就拿到梯度。）
Format compliance carries a low weight so clean formatting never outweighs good play.（格式合规占的权重很低，所以干净的格式永远压不过好的棋力。）
The invalid move penalty is capped so one broken game can't drown out everything the model did right.（非法走法的惩罚是有上限的，这样一局崩掉的棋不会淹没掉模型做对的所有事情。）

Wiring it together（把它们接起来）
def load_environment(min_random_move_prob, max_random_move_prob, parse_think):
    dataset = generate_games(min_random_move_prob, max_random_move_prob)
    parser = XMLParser(fields=["think", "move"])
    rubric = Rubric(funcs=[...], weights=[1.0, 1.0, 0.2, 1.0])
    return OthelloEnv(dataset, parser, rubric)

What the numbers show（数据说明了什么）
prime eval run othello -m openai/gpt-4.1 -n 100 \
  -a '{"min_random_move_prob": 0.0, "max_random_move_prob": 0.0, "minimax_depth": 3}'

From evaluation to training（从评估到训练）
prime eval run othello -m openai/gpt-4.1 -n 200 \
  --save-to-hf-hub --hf-hub-dataset-name your-username/othello-data

for prompt in batch:
    rollouts = [play_game(model, prompt) for _ in range(group_size)]
    rewards = [total_reward(r.final_state) for r in rollouts]
    advantage = rewards - mean(rewards)     # relative to the group
    update_model(model, rollouts, advantage)

Adapting this to your own task（把它适配到你自己的任务）
class TaskEnv(MultiTurnEnv):
    def env_response(self, model_output, state):
        action = parse_action(model_output)          # your task's syntax
        if not is_valid(action, state):
            return error_message(action), penalize(state)
        state = apply_action(state, action)          # your task's rules
        if not task_complete(state):
            state = environment_step(state)          # tool, API call, or opponent
        return render_state(state), state            # your task's display

Task logic：your domain's rules for what counts as a valid action and how the state changes（任务逻辑：你这个领域里，什么算作一个合法的 action、状态又是如何变化的规则）
Response engine：whatever the model reacts to, from a rule-based simulator to a live API to another model（响应引擎：任何模型所反应的对象，从基于规则的模拟器，到实时的 API，再到另一个模型）
Reward functions：keep the pattern (outcome signal, partial credit, format, penalty) and replace the domain logic（奖励函数：保留这个套路——结果信号、部分给分、格式、惩罚——只替换掉领域逻辑）
State rendering：whatever the model needs to see, whether that's a file diff, a conversation transcript, or a tool's response（状态渲染：模型需要看到的任何东西，无论是文件 diff、对话转录，还是某个工具的返回）

Try it yourself（自己动手试）
