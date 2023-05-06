"""
米游社相关
"""
import json
import random
import re
import string
import sys
import time

import httpx

from . import user_global_var as gl, logger
from .com_tool import md5_encode
from .data_class import UserInfo, GameInfo, ClassEncoder

MYS_SALT = "TsmyHpZg8gFAVKTtlPaL6YwMldzxZJxQ"
MYS_SALT_TWO = "t0qEgfub6cvueAPgR5m9aQWWVciEer7v"
MYS_SALT_WEB = "osgT0DljLarYxgebPPHJFjdaxPfoiHGt"
MYS_CHANNEL = {
    "1": "崩坏3",
    "2": "原神",
    "3": "崩坏学园2",
    "4": "未定事件簿",
    "5": "米游社",
    "6": "崩坏：星穹铁道",
    "8": "绝区零"
}
GAME_NAME = {
    "bh2_cn": "崩坏2",
    "bh3_cn": "崩坏3",
    "nxx_cn": "未定事件簿",
    "hk4e_cn": "原神",
    "hkrpg_cn": "崩坏：星穹铁道"
}


async def get_new_ds(_b, _q):
    """
    生成请求 Header 里的 DS
    参考：
    https://github.com/Womsxd/MihoyoBBSTools/blob/master/tools.py
    https://github.com/Womsxd/MihoyoBBSTools/blob/master/setting.py
    https://loliurl.club/383.html
    保留此函数以备后用
    """
    try:
        t_param = str(int(time.time()))
        r_param = str(random.randint(100001, 200000))
        b_param = '传入参数, 待查明'
        q_param = '传入参数, 待查明'
        c_param = md5_encode(f"salt={MYS_SALT_TWO}&t={t_param}&r={r_param}&b={b_param}&q={q_param}")
        return f"{t_param},{r_param},{c_param}"
    except KeyboardInterrupt:
        logger.warning("用户强制退出")
        input("按回车键继续")
        sys.exit()
    except Exception as err:
        logger.error(f"运行出错, 错误为: {err}, 错误行数为: {err.__traceback__.tb_lineno}")
        return None


async def get_old_ds(web: bool):
    """
    生成请求 Header 里的 DS
    参考：
    https://github.com/Womsxd/MihoyoBBSTools/blob/master/tools.py
    https://github.com/Womsxd/MihoyoBBSTools/blob/master/setting.py
    保留此函数以备后用
    """
    if web:
        old_salt = MYS_SALT_WEB
    else:
        old_salt = MYS_SALT
    t_param = str(int(time.time()))
    r_param = ''.join(random.sample(string.ascii_lowercase + string.digits, 6))
    c_param = md5_encode(f'salt={old_salt}&t={t_param}&r={r_param}')
    return f"{t_param},{r_param},{c_param}"


async def update_cookie(account: UserInfo):
    """
    更新cookie
    需要stoken
    """
    try:
        if account.stoken == "" or account.mys_uid == "":
            logger.warning("缺少stoken或账户ID，请重新获取cookie")
            return False
        update_cookie_url = gl.mi_url + "/auth/api/getCookieAccountInfoBySToken"
        update_cookie_url_params = {
            "uid": account.mys_uid,
            "stoken": account.stoken
        }
        logger.info("开始更新cookie")
        async with httpx.AsyncClient() as client:
            update_cookie_url_req = await client.get(update_cookie_url, params=update_cookie_url_params)
        update_cookie_url_req = update_cookie_url_req.json()
        if update_cookie_url_req['data'] is None:
            logger.error(f"cookie获取出错，错误原因为: {update_cookie_url_req['message']}")
            return False
        account.cookie = re.sub(account.cookie_token, update_cookie_url_req['data']['cookie_token'], account.cookie)
        with open(gl.user_data_path / f"{account.mys_uid}.json", 'w',
                  encoding='utf-8') as f:
            json.dump(account, f, ensure_ascii=False, indent=4, cls=ClassEncoder)
        return account.cookie
    except KeyboardInterrupt:
        logger.warning("用户强制退出")
        input("按回车键继续")
        sys.exit()
    except Exception as err:
        logger.error(f"运行出错, 错误为: {err}, 错误行数为: {err.__traceback__.tb_lineno}")
        return False


async def get_point(account: UserInfo):
    """
    获取米游币数量
    需要stoken与stuid
    """
    try:
        if account.stoken == "" or account.stuid == "":
            logger.warning("缺少stoken或stuid，请重新获取cookie")
            return False
        point_url = gl.bbs_url + '/apihub/sapi/getUserMissionsState'
        point_headers = {
            'Cookie': account.cookie,
        }
        async with httpx.AsyncClient() as client:
            point_req = await client.get(point_url, headers=point_headers)
        if point_req.status_code != 200:
            logger.error(f"获取米游币数量失败, 返回状态码为{str(point_req.status_code)}")
            return False
        point_req = point_req.json()
        if point_req['retcode'] != 0:
            logger.error(f"获取米游币数量失败, 原因为{point_req['message']}")
            return False
        return point_req['data']['total_points']
    except Exception as err:
        logger.error(f"运行出错, 错误为: {err}, 错误行数为: {err.__traceback__.tb_lineno}")
        return False


async def check_cookie(account: UserInfo) -> int:
    """
    检查cookie是否过期
    """
    try:
        check_cookie_url = gl.mi_url + '/account/address/list'
        check_cookie_hearders = {
            'Cookie': account.cookie
        }
        async with httpx.AsyncClient() as client:
            check_cookie_req = await client.get(check_cookie_url, headers=check_cookie_hearders)
        if check_cookie_req.status_code != 200:
            logger.error(f"检查Cookie失败, 返回状态码为{str(check_cookie_req.status_code)}")
            return -1
        check_cookie_req = check_cookie_req.json()
        if check_cookie_req['retcode'] != 0:
            logger.warning("Cookie已过期")
            return 0
        return 1
    except KeyboardInterrupt:
        logger.warning("用户强制退出")
        input("按回车键继续")
        sys.exit()
    except Exception as err:
        logger.error(f"运行出错, 错误为: {err}, 错误行数为: {err.__traceback__.tb_lineno}")
        return -1


# 需优化
async def get_goods_detail(goods_id, get_type=''):
    """
    按需要获取礼物详情
    """
    try:
        goods_detail_url = gl.mi_url + "/mall/v1/web/goods/detail"
        goods_detail_params = {
            "app_id": 1,
            "point_sn": "myb",
            "goods_id": goods_id,
        }
        async with httpx.AsyncClient() as client:
            goods_detail_req = await client.get(goods_detail_url, params=goods_detail_params)
        if goods_detail_req.status_code != 200:
            return [False, False]
        goods_detail = goods_detail_req.json()["data"]
        if goods_detail is None:
            return [False, False]
        if get_type == "status":
            if not goods_detail['unlimit'] and goods_detail['next_num'] == 0 and goods_detail['total'] == 0:
                return [-1, goods_detail['goods_name']]
            return [True, goods_detail['goods_name']]
        return_info = [goods_detail['game_biz'], goods_detail['type'], goods_detail['rules']]
        if goods_detail['status'] == 'online':
            return_info.append(int(goods_detail['next_time']))
            return return_info
        return_info.append(int(goods_detail['sale_start_time']))
        return return_info
    except KeyboardInterrupt:
        logger.warning("用户强制退出")
        input("按回车键继续")
        sys.exit()
    except Exception as err:
        logger.error(f"运行出错, 错误为: {err}, 错误行数为: {err.__traceback__.tb_lineno}")
        return False


async def get_action_ticket(account: UserInfo):
    """
    获取查询所需 ticket
    需要stoken与账户ID
    """
    try:
        if account.stoken == "" or account.mys_uid == "":
            logger.warning("缺少stoken或账户ID，请重新获取cookie")
            return False
        action_ticket_url = gl.mi_url + "/auth/api/getActionTicketBySToken"
        action_ticket_params = {"action_type": "game_role", "stoken": account.stoken, "uid": account.mys_uid}
        async with httpx.AsyncClient() as client:
            action_ticket_req = await client.get(action_ticket_url, params=action_ticket_params)
        if action_ticket_req.status_code != 200:
            logger.error(
                f"ticket请求失败, 请检查cookie, 返回状态码为{str(action_ticket_req.status_code)}")
            return False
        if action_ticket_req.json()['data'] is None:
            logger.error(f"ticket获取失败, 原因为{action_ticket_req.json()['message']}")
            return False
        return action_ticket_req.json()['data']['ticket']
    except KeyboardInterrupt:
        logger.warning("用户强制退出")
        input("按回车键继续")
        sys.exit()
    except Exception as err:
        logger.error(f"运行出错, 错误为: {err}, 错误行数为: {err.__traceback__.tb_lineno}")
        return False


async def check_game_roles(account: UserInfo, game_biz='', uid=0, get_type='get'):
    """
    检查绑定角色
    """
    try:
        action_ticket = await get_action_ticket(account)
        if not action_ticket:
            return False
        game_roles_url = gl.mi_url + "/binding/api/getUserGameRoles"
        game_roles_params = {"point_sn": "myb", "action_ticket": action_ticket}
        if get_type == 'check':
            game_roles_params['uid'] = uid
        game_roles_headers = {"cookie": account.cookie}
        async with httpx.AsyncClient() as client:
            game_roles_req = await client.get(game_roles_url,
                                              headers=game_roles_headers,
                                              params=game_roles_params)
        if game_roles_req.status_code != 200:
            logger.error(
                f"检查绑定角色请求失败, 请检查传入参数, 返回状态码为{str(game_roles_req.status_code)}")
            return False
        game_roles_req = game_roles_req.json()
        if game_roles_req['retcode'] != 0:
            logger.error(f"检查绑定角色失败, 原因为{game_roles_req['message']}")
            return False
        game_roles_list = game_roles_req['data']['list']
        if not game_roles_list:
            logger.info('没有绑定任何角色')
            return False
        if get_type == 'get':
            game_roles_new_list = []
            for game_roles in game_roles_list:
                game_roles_new_dict = {'game_biz': game_roles['game_biz'],
                                       'game_uid': game_roles['game_uid'],
                                       'game_nickname': game_roles['nickname'],
                                       'game_level': game_roles['level'],
                                       'game_region': game_roles['region'],
                                       'game_region_name': game_roles['region_name']}
                game_roles_new_list.append(GameInfo(**game_roles_new_dict))
            return game_roles_new_list
        for game_roles in game_roles_list:
            if game_roles['game_biz'] == game_biz and game_roles['game_uid'] == str(uid):
                return True
        logger.info('没有绑定该游戏角色')
        return False
    except KeyboardInterrupt:
        logger.warning("用户强制退出")
        input("按回车键继续")
        sys.exit()
    except Exception as err:
        logger.error(f"运行出错, 错误为: {err}, 错误行数为: {err.__traceback__.tb_lineno}")
        return False
