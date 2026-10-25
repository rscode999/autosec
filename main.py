import combine 
import outlook 
import slack

if __name__ == '__main__':
    with open("auth/tokens.txt", 'r') as f:
        auth_args = f.read().split("\n")

    slack.main(['', auth_args[0], auth_args[1]])
    combine.main()
    outlook.main(['', auth_args[2]])