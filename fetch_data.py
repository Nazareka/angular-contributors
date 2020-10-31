import aiohttp
from aiohttp import ClientSession
import asyncio
import json
import math as m
import aioschedule as schedule
import time
from typing import Coroutine, Any

async def async_fetch_data_with_parse(session: ClientSession, url: str):
    headers = {'Authorization': 'token "token"'}
    async with session.get(url, headers=headers) as response:
        return await response.json(content_type=None)

async def get_angular_organization(session: ClientSession):
    url = 'https://api.github.com/orgs/angular'
    return await async_fetch_data_with_parse(session, url)

async def get_angular_repositories(session: ClientSession, per_page: int, page: int) :
    url = 'https://api.github.com/orgs/angular/repos?per_page={}&page={}'.format(per_page, page)
    return await async_fetch_data_with_parse(session, url)

async def get_contributes_by_repositories(session: ClientSession, repos: str, per_page: int, page: int):
    url = 'https://api.github.com/repos/angular/{}/contributors?per_page={}&page={}'.format(repos, per_page, page)
    return await async_fetch_data_with_parse(session, url)

async def get_user_profile_by_login(session: ClientSession, login: str):
    url = 'https://api.github.com/users/{}'.format(login)
    return await async_fetch_data_with_parse(session, url)

async def fetch_cuntributors_data():
    async with aiohttp.ClientSession() as session:
        print('start')
        Angular_org_data = await get_angular_organization(session)
        count_public_repos = Angular_org_data["public_repos"]  
        reposes = []

        for i in range(1, m.ceil(float(count_public_repos) / 100) + 1):
            reposes = reposes + await get_angular_repositories(session, 100, i)
            print(i, 'loadrepos')
        contributors_list = []
        tasks = []
        for repos in reposes:
            page = 0
            while True:
                page = page + 1
                if(data := await get_contributes_by_repositories(session, repos["name"], 100, page)) != []:
                    try:
                        contributors_list = contributors_list + data
                        print(page, repos["name"], len(data))
                    except:
                        break
                else:
                    break
        contributors_profiles_list = []
        counter_contributors_list = []
                
        set_of_logins_contributors: set[str] = set()
        print('counting contributions', len(contributors_list))
        for contributor in contributors_list:
            if not(contributor["login"] in set_of_logins_contributors):
                set_of_logins_contributors.add(contributor["login"])
                counter_contributors_list.append({
                    "login": contributor["login"],
                    "contributions": int(contributor["contributions"])
                })
                
            else:
                for i, counter_contributor in enumerate(counter_contributors_list):
                    if counter_contributor["login"] == contributor["login"]:
                        counter_contributors_list[i]["contributions"] += int(contributor["contributions"])
                        break
        tasks: list[Coroutine[Any, Any, Any]] = []
        for contrib in counter_contributors_list:
            tasks.append(get_user_profile_by_login(session, contrib["login"]))
        responses = await asyncio.gather(*(task for task in tasks))

        for contributor_profile_data in responses:
            for i, counter_contributor in enumerate(counter_contributors_list):
                try:
                    if counter_contributor["login"] == contributor_profile_data["login"]:
                        contributors_profiles_list.append({
                            **contributor_profile_data,
                            "contributions": counter_contributors_list[i]["contributions"]
                        })
                        break
                except KeyError:
                    print('KeyError')
                    pass
        with open('data.json', 'w') as outfile:
            json.dump(contributors_profiles_list, outfile)


if __name__ == '__main__':
    print('started')
    loop = asyncio.get_event_loop()
    loop.run_until_complete(fetch_cuntributors_data())
    schedule.every().hour.do(fetch_cuntributors_data)
    loop = asyncio.get_event_loop()
    while True:
        loop.run_until_complete(schedule.run_pending())
        time.sleep(0.1)
