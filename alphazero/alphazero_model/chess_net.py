import torch
import torch.nn as nn
import torch.nn.functional as F


class ResidualBlock(nn.Module):
    def __init__(self, in_channels, out_channels, kernel_size=3, stride=1):
        super().__init__()
        self.conv1 = nn.Conv2d(in_channels, out_channels, kernel_size=kernel_size, stride=stride, padding=1)
        self.bn1 = nn.BatchNorm2d(out_channels)
        self.conv2 = nn.Conv2d(out_channels, out_channels, kernel_size=kernel_size, stride=stride, padding=1)
        self.bn2 = nn.BatchNorm2d(out_channels)
        self.relu = nn.ReLU(inplace=True)

    def forward(self, x):
        identity = x
        out = self.conv1(x)
        out = self.bn1(out)
        out = self.relu(out)

        out = self.conv2(out)
        out = self.bn2(out)

        out += identity
        out = self.relu(out)
        return out


class ChessNet(nn.Module):
    def __init__(self, in_channels=16, res_channels=64, num_res_blocks=5):
        super().__init__()
        self.conv = nn.Conv2d(in_channels, res_channels, kernel_size=3, stride=1, padding=1)
        self.bn = nn.BatchNorm2d(res_channels)
        self.relu = nn.ReLU(inplace=True)

        res_blocks = []
        for i in range(num_res_blocks):
            res_blocks.append(ResidualBlock(res_channels, res_channels))
        self.res_blocks = nn.Sequential(*res_blocks)

        self.policy_conv = nn.Conv2d(64, 2, kernel_size=1)
        self.policy_bn = nn.BatchNorm2d(2)
        self.policy_fc = nn.Linear(2 * 8 * 8, 64 * 8 * 8)

        self.value_conv = nn.Conv2d(64, 64, kernel_size=1)
        self.value_bn = nn.BatchNorm2d(64)
        self.value_fc = nn.Linear(64 * 8 * 8, 256)
        self.value_fc2 = nn.Linear(256, 1)

    def forward(self, x):
        x = self.conv(x)
        x = self.bn(x)
        x = self.relu(x)

        x = self.res_blocks(x)

        policy = self.policy_conv(x)
        policy = self.policy_bn(policy)
        policy = self.relu(policy)
        policy = policy.reshape(-1, 2 * 8 * 8)
        policy = self.policy_fc(policy)

        value = self.value_conv(x)
        value = self.value_bn(value)
        value = self.relu(value)
        value = value.reshape(-1, 64 * 8 * 8)
        value = F.relu(self.value_fc(value))
        value = torch.tanh(self.value_fc2(value))

        return policy, value


if __name__ == "__main__":
    state = torch.randn((32, 8, 8, 16)).permute(0, 3, 1, 2)
    model = ChessNet()
    policy, value = model(state)
    policy = torch.softmax(policy, dim=1).squeeze(0).detach().cpu().numpy()
    print(policy, value[0][0])
