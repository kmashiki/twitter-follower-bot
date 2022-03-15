import tweepy
import click
import json

import creds

#########################
########## CLI ##########
#########################

@click.command()
@click.option('--username', '-u', help='Username for person you want to look for likely followers from their following list')
@click.option('--floor_threshold', '-f', default=1, help='Ratio of following to followers that is the bottom threshold for including a user in to-be-followed list')
@click.option('--cieling_threshold', '-c', default=4, help='Ratio of following to followers that is the top threshold for including a user in to-be-followed list')
def run_bot(username, floor_threshold, cieling_threshold):
    print(f'username: {username}')

    client = tweepy.Client(bearer_token=creds.BEARER_TOKEN, wait_on_rate_limit=True)
    
    # get id from username. check cache first
    with open('user_cache.json', 'r') as f:
        user_cache = json.load(f)
        user_id = user_cache.get(username)
        if user_id is None:
            print('Getting user from Twitter')
            user = client.get_user(username=username)
            user_id = user.data.id
        print(f'user_id: {user_id}')
    
    following = get_following(client, user_id, username)
    print(f'{username} is following {len(following)} users')
    
    users_to_follow = []
    # loop through each follower f
    for f in following:
        print(f.get('name'))
        user = client.get_user(id=f.get('id'), user_fields=['public_metrics'])
        user_public_metrics = user.data.get('public_metrics')
        num_following = user_public_metrics.get('following_count')
        num_followers = user_public_metrics.get('followers_count')
        ratio = float(num_following) / num_followers # find ratio r of following to follower for f

        print(f'ratio: {ratio}')
        
        if ratio > floor_threshold and ratio < cieling_threshold: # if r > some value, add to array
            users_to_follow.append(f)
        
    
    # print array of users to follow (likely to follow you back)
    print(users_to_follow)
    usernames_to_follow = [user.get('username') for user in users_to_follow]
    print(usernames_to_follow)


def get_following(client, user_id, username):
    # get users this person is following. check cache first
    try:
        with open(f'{username}_following_cache.json', 'r') as cache_file:
            following = json.load(cache_file)
            print(f'Getting {username}\'s Following from cache')
            return following
    except:
        print(f'Getting users {username} is following via API')
        following = paginate_users_endpoint(client, user_id, 'following')
        with open(f'{username}_following_cache.json', 'w') as cache_file:
            following_parsed = []
            for f in following:
                following_parsed.append({
                    'id': f.data.get('id'),
                    'username': f.data.get('username'),
                    'name': f.data.get('name')
                })
            cache_file.write(json.dumps(following_parsed))

            return following_parsed
    

# def get_followers(client, user_id, username):
#     # get users this person is following. check cache first
#     try:
#         with open(f'{username}_follower_cache.json', 'r') as cache_file:
#             followers = json.load(cache_file)
#             print(f'Getting {username}\'s Follower from cache')
#             return followers
#     except:
#         print(f'Getting {username}\'s followers via API')
#         followers = paginate_users_endpoint(client, user_id, 'followers')
#         with open(f'{username}_follower_cache.json', 'w') as cache_file:
#             followers_parsed = []
#             for f in followers:
#                 followers_parsed.append({
#                     'id': f.data.get('id'),
#                     'username': f.data.get('username'),
#                     'name': f.data.get('name')
#                 })
#             cache_file.write(json.dumps(followers_parsed))
        
#         return followers_parsed

def paginate_users_endpoint(client, user_id, endpoint):
    all_following = []
    if endpoint == 'following':
        response = client.get_users_following(id=user_id, pagination_token=None)
    elif endpoint == 'followers':
        response = client.get_users_followers(id=user_id, pagination_token=None)
    next_pagination_token = response.meta.get('next_token')
    all_following.extend(response.data)
    
    while next_pagination_token is not None:
        if endpoint == 'following':
            response = client.get_users_following(id=user_id, pagination_token=next_pagination_token)
        elif endpoint == 'followers':
            response = client.get_users_followers(id=user_id, pagination_token=next_pagination_token)
        next_pagination_token = response.meta.get('next_token')
        all_following.extend(response.data)
    
    return all_following

if __name__ == '__main__':
    run_bot()