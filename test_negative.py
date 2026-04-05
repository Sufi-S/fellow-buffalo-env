from environment import FellowBuffaloEnv
from models import FellowBuffaloAction

# Create environment
env = FellowBuffaloEnv()

# Reset Task 1
obs = env.reset(task_id=1)
print(f'Email: {obs.email_subject}')
print(f'Correct tab should be: {obs.metadata.get("correct_tab", "unknown") if hasattr(obs, "metadata") else "unknown"}')

# Create a WRONG action
wrong_action = FellowBuffaloAction(
    task_id=1,
    tab='WrongTab',  # Wrong tab
    color='purple',   # Wrong color
    deadline='2999-01-01',
    confidence=95
)

# Take step
obs, reward, done = env.step(wrong_action)
print(f'\nReward from step(): {reward}')
print(f'Expected: Negative (around -0.3 to -0.5)')

if reward < 0:
    print('\n✅ SUCCESS! Negative scores working!')
else:
    print(f'\n❌ Got {reward}, expected negative')