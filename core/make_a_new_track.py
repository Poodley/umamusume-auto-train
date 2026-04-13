import os
import re

import Levenshtein
import pyautogui

import core.state as state
import utils.constants as constants
from core.ocr import extract_number, extract_text
from core.recognizer import match_template, is_btn_active
from utils.screenshot import enhanced_screenshot
from utils.log import info, warning
from utils.tools import drag_scroll, get_secs, sleep


ITEM_ASSET_ROOT = os.path.join("assets", "items", "make_a_new_track")
BUTTON_ASSETS = {
  "shop": os.path.join(ITEM_ASSET_ROOT, "shop.png"),
  "open_items": os.path.join(ITEM_ASSET_ROOT, "buttons", "open_items.png"),
  "close_items": os.path.join(ITEM_ASSET_ROOT, "buttons", "close_items.png"),
  "shop_checkbox": os.path.join(ITEM_ASSET_ROOT, "check_box.png"),
  "confirm_purchase": os.path.join(ITEM_ASSET_ROOT, "confirm.png"),
  "back": os.path.join("assets", "buttons", "back_btn.png"),
  "close": os.path.join("assets", "buttons", "close_btn.png"),
}
ITEM_ASSETS = {
  "empowering_megaphone": os.path.join(ITEM_ASSET_ROOT, "empowering_megaphone.png"),
  "small_energy": os.path.join(ITEM_ASSET_ROOT, "small_energy.png"),
  "medium_energy": os.path.join(ITEM_ASSET_ROOT, "medium_energy.png"),
  "large_energy": os.path.join(ITEM_ASSET_ROOT, "large_energy.png"),
  "super_cupcake": os.path.join(ITEM_ASSET_ROOT, "super_cupcake.png"),
  "cupcake": os.path.join(ITEM_ASSET_ROOT, "cupcake.png"),
  "glowstick": os.path.join(ITEM_ASSET_ROOT, "glowstick.png"),
  "kale_juice": os.path.join(ITEM_ASSET_ROOT, "kale_juice.png"),
  "fortune_charm": os.path.join(ITEM_ASSET_ROOT, "fortune_charm.png"),
  "hand_cream": os.path.join(ITEM_ASSET_ROOT, "hand_cream.png"),
  "all_cure": os.path.join(ITEM_ASSET_ROOT, "all_cure.png"),
  "gold_race_hammer": os.path.join(ITEM_ASSET_ROOT, "gold_race_hammer.png"),
  "silver_race_hammer": os.path.join(ITEM_ASSET_ROOT, "silver_race_hammer.png"),
  "stamina_scroll": os.path.join(ITEM_ASSET_ROOT, "stamina_scroll.png"),
  "speed_scroll": os.path.join(ITEM_ASSET_ROOT, "speed_scroll.png"),
  "power_scroll": os.path.join(ITEM_ASSET_ROOT, "power_scroll.png"),
  "guts_scroll": os.path.join(ITEM_ASSET_ROOT, "guts_scroll.png"),
  "wit_scroll": os.path.join(ITEM_ASSET_ROOT, "wit_scroll.png"),
  "stamina_manual": os.path.join(ITEM_ASSET_ROOT, "stamina_manual.png"),
  "speed_manual": os.path.join(ITEM_ASSET_ROOT, "speed_manual.png"),
  "power_manual": os.path.join(ITEM_ASSET_ROOT, "power_manual.png"),
  "guts_manual": os.path.join(ITEM_ASSET_ROOT, "guts_manual.png"),
  "wit_manual": os.path.join(ITEM_ASSET_ROOT, "wit_manual.png"),
  "speed_bracelet": os.path.join(ITEM_ASSET_ROOT, "speed_bracelet.png"),
  "stamina_bracelet": os.path.join(ITEM_ASSET_ROOT, "stamina_bracelet.png"),
  "power_bracelet": os.path.join(ITEM_ASSET_ROOT, "power_bracelet.png"),
  "guts_bracelet": os.path.join(ITEM_ASSET_ROOT, "guts_bracelet.png"),
}
ITEM_NAMES = ["vita 20", "vita 40", "vita 65", "empowering megaphone", "royal kale juice",
              "stamina scroll", "speed scroll", "power scroll", "guts scroll", "wit scroll", 
              "stamina manual", "speed manual", "power manual", "guts manual", "wit manual", "speed bracelet", 
              "stamina ankle weights", "power ankle weights", "guts ankle weights", 
              "berry sweet cupcake", "plain cupcake", "reset whistle", "grilled carrots",
              "good-luck charm", "rich hand cream", "miracle cure", "artisan cleat hammer", "master cleat hammer"]
ITEM_ALIASES = {
  "megaphone": ["empowering_megaphone"],
  "race_hammer": ["gold_race_hammer", "silver_race_hammer"],
  "energy": ["small_energy", "medium_energy", "large_energy", "super_cupcake", "cupcake", "kale_juice"],
  "bracelet": ["speed_bracelet", "stamina_bracelet", "power_bracelet", "guts_bracelet"],
}
BRACELET_BY_TRAINING = {
  "spd": "speed_bracelet",
  "sta": "stamina_bracelet",
  "pwr": "power_bracelet",
  "guts": "guts_bracelet",
}
CONDITION_ITEM_BY_NAME = {
  "Skin Outbreak": "hand_cream",
}
buy_list:list[tuple[str, int]] = []
runtime_state = {
  "bought_counts": {
    "vita 20": 0,
    "vita 40": 0,
    "vita 65": 0,
    "empowering megaphone": 0,
    "royal kale juice": 0,
    "stamina ankle weights": 0,
    "power ankle weights": 0,
    "guts ankle weights": 0,
    "berry sweet cupcake": 0,
    "plain cupcake": 0,
    "reset whistle": 0,
    "grilled carrots": 0,
    "good-luck charm": 0,
    "rich hand cream": 0,
    "miracle cure": 0,
    "artisan cleat hammer": 0,
    "master cleat hammer": 0
  },
  "used_items": [],
  "used_items_this_turn": set(),
  "shop_checked_this_turn": False,
  "shop_visited_this_turn": False,
  "summer_turn_counter": 0,
  "last_turn_key": None,
  "missing_assets_logged": set(),
}


def reset_runtime_state():
  runtime_state["bought_counts"] = {
    "megaphone": 0,
    "bracelet": 0,
  }
  runtime_state["used_items"] = []
  runtime_state["used_items_this_turn"] = set()
  runtime_state["shop_visited_this_turn"] = False
  runtime_state["summer_turn_counter"] = 0
  runtime_state["last_turn_key"] = None
  runtime_state["missing_assets_logged"] = set()


def get_settings():
  return state.MAKE_A_NEW_TRACK if isinstance(state.MAKE_A_NEW_TRACK, dict) else {}


def is_enabled():
  return bool(get_settings().get("enabled", False))


def _log_missing_asset_once(path):
  if path in runtime_state["missing_assets_logged"]:
    return
  runtime_state["missing_assets_logged"].add(path)
  warning(f"Make A New Track asset missing: {path}")


def _asset_exists(path):
  exists = os.path.exists(path)
  if not exists:
    _log_missing_asset_once(path)
  return exists


def _find_template(path, region=None, threshold=0.9, use_cache=False):
  if not _asset_exists(path):
    return []
  return match_template(path, region=region, threshold=threshold, use_cache=use_cache)


def _offset_box(box, region):
  left, top = region[0], region[1]
  x, y, w, h = box
  return (x + left, y + top, w, h)


def _to_pyautogui_region(region):
  left, top, right, bottom = region
  return (left, top, right - left, bottom - top)


def _get_shop_list_region():
  region = get_settings().get("shop_list_region")
  if isinstance(region, dict) and all(key in region for key in ("left", "top", "right", "bottom")):
    return (region["left"], region["top"], region["right"], region["bottom"])
  return (250, 395, 855, 810)


def _get_shop_confirm_region():
  region = get_settings().get("shop_confirm_region")
  if isinstance(region, dict) and all(key in region for key in ("left", "top", "right", "bottom")):
    return (region["left"], region["top"], region["right"], region["bottom"])
  return (420, 860, 690, 955)


def _resolve_item_names(item_name):
  resolved_names = ITEM_ALIASES.get(item_name, [item_name])
  if item_name == "bracelet":
    allowed_bracelets = set(get_settings().get("allowed_bracelets", resolved_names))
    return [name for name in resolved_names if name in allowed_bracelets]
  return resolved_names


def _click_box(box):
  x, y, w, h = box
  pyautogui.moveTo(x + w // 2, y + h // 2, duration=0.15)
  pyautogui.click()
  sleep(0.2)


def _confirm_shop_purchase():
  confirm_asset = BUTTON_ASSETS["confirm_purchase"]
  if not _asset_exists(confirm_asset):
    return False
  button = pyautogui.locateOnScreen(
    confirm_asset,
    confidence=0.85,
    minSearchTime=get_secs(0.7),
    region=_to_pyautogui_region(_get_shop_confirm_region()),
  )
  if not button:
    return False
  _click_box(button)
  return True


def _open_shop():
  shop_asset = BUTTON_ASSETS["shop"]
  if not _asset_exists(shop_asset):
    return False
  button = pyautogui.locateOnScreen(shop_asset, confidence=0.85, minSearchTime=get_secs(0.7))
  if not button:
    return False
  _click_box(button)
  sleep(0.3)
  return True



def _close_shop():
  for button_name in ("back", "close"):
    button_asset = BUTTON_ASSETS[button_name]
    if not _asset_exists(button_asset):
      continue
    button = pyautogui.locateOnScreen(button_asset, confidence=0.85, minSearchTime=get_secs(0.5))
    if not button:
      continue
    _click_box(button)
    sleep(0.2)
    return True
  return False


def _get_turns_left_region(box):
  settings = get_settings()
  offset = settings.get("shop_turns_left_offset", {
    "x": 0,
    "y": -36,
    "w": 70,
    "h": 36,
  })
  x, y, w, h = box
  return (
    x + offset["x"],
    y + offset["y"],
    offset["w"],
    offset["h"],
  )


def _get_turns_left_for_box(box):
  try:
    region = _get_turns_left_region(box)
    turns_image = enhanced_screenshot(region)
    turns_left = extract_number(turns_image)
    if turns_left == -1:
      return 999
    return turns_left
  except Exception:
    return 999




def _open_items_menu():
  open_asset = BUTTON_ASSETS["open_items"]
  if not _asset_exists(open_asset):
    return False
  button = pyautogui.locateOnScreen(open_asset, confidence=0.85, minSearchTime=get_secs(0.7))
  if not button:
    return False
  _click_box(button)
  return True


def _close_items_menu():
  close_asset = BUTTON_ASSETS["close_items"]
  if not _asset_exists(close_asset):
    return False
  button = pyautogui.locateOnScreen(close_asset, confidence=0.85, minSearchTime=get_secs(0.3))
  if not button:
    return False
  _click_box(button)
  return True

def use_grilled_carrots():
  use_grilled_carrots_pic = os.path.join(ITEM_ASSET_ROOT, "use_grilled_carrot.png")
  if not _asset_exists(use_grilled_carrots_pic):
    return False
  button = pyautogui.locateOnScreen(use_grilled_carrots_pic, confidence=0.85, minSearchTime=get_secs(0.7))
  return _use_item("grilled carrots")

def _use_item(item_name):
  if not _open_items_menu():
    return False

  for resolved_item_name in _resolve_item_names(item_name):
    item_path = ITEM_ASSETS.get(resolved_item_name)
    if not item_path:
      continue

    matches = _find_template(item_path, threshold=0.88)
    if not matches:
      continue

    info(f"Using Make A New Track item: {resolved_item_name}")
    _click_box(matches[0])
    pyautogui.press("enter")
    sleep(0.3)
    runtime_state["used_items"].append(resolved_item_name)
    runtime_state["used_items_this_turn"].add(item_name)
    runtime_state["used_items_this_turn"].add(resolved_item_name)
    _close_items_menu()
    return True

  _close_items_menu()
  return False


def _has_item(item_name):
  if not _open_items_menu():
    return False

  matches = []
  for resolved_item_name in _resolve_item_names(item_name):
    item_path = ITEM_ASSETS.get(resolved_item_name)
    if not item_path:
      continue
    matches = _find_template(item_path, threshold=0.88)
    if matches:
      break

  _close_items_menu()
  return bool(matches)


def current_counts():
  return runtime_state["bought_counts"]


def can_buy(item_name):
  caps = get_settings().get("item_caps", {})
  cap = caps.get(item_name)
  if cap is None:
    return True
  return runtime_state["bought_counts"].get(item_name, 0) < cap


def register_purchase(item_name):
  if item_name in runtime_state["bought_counts"]:
    runtime_state["bought_counts"][item_name] += 1
    

def check_shop():
  global buy_list
  # Checks the shop for items and updates the buy_list with the turns left for each item. This is used to determine which item to buy when visiting the shop later in the turn. Buying is handled in maybe_buy_from_shop() which checks the buy_list to see if any items are available to buy and buys them if they are.
  if not is_enabled():
    return False
  if runtime_state["shop_checked_this_turn"]:
    return False
  shop_priority = get_settings().get("shop_priority", [])
  if not shop_priority:
    return False
  if not _open_shop():
    return False
  seen = set()
  runtime_state["shop_checked_this_turn"] = True
  for i in range(5):
    if state.stop_event.is_set():
      return False
    if i > 8:
      sleep(0.5)
    buy_item_icon = match_template("assets\\items\\make_a_new_track\\check_box.png", threshold=0.9, use_cache = False)

    if buy_item_icon:
      for x, y, w, h in buy_item_icon:
        # The item name isn't directly on the shop screen, so we have to take a screenshot of the area around the checkbox and do OCR to determine which item it is
        region = (x - 420, y - 40, w + 275, h + 5)
        screenshot = enhanced_screenshot(region)
        text = extract_text(screenshot)
        turn_region = (x-10, y-40, w-30, h-5)
        turn_region = enhanced_screenshot(turn_region)
        turns_number = extract_number(turn_region)
        # attempt to avoid duplicates? doesn't work well because of OCR inconsistencies but might as well try. This is to avoid having multiple entries for the same item with different turns left values 
        # due to OCR reading the item name slightly differently each time.
        key = (round(y / 10), text)
        if key in seen:
          continue
        seen.add(key)
        if is_item_match(text, ITEM_NAMES):
          # TODO: only buy grilled carrots if bond is not orange
          buy_list.append((text, turns_number))
          info(f"Turns left for {text}: {turns_number}")

    drag_scroll(constants.SHOP_SCROLL_BOTTOM_MOUSE_POS, -450)
    sleep(0.3)
  pyautogui.moveTo(constants.SCROLLING_SHOP_MOUSE_POS)
  # get rid of duplicates in buy_list just in case
  buy_list = list(set(buy_list))
  # sort buy_list by turns left so that items with the least turns left are bought first
  buy_list.sort(key=lambda x: x[1])
  info(f"Shop check complete. Buy list: {buy_list}")
  _close_shop()
  return True

def maybe_buy_from_shop():
  if not is_enabled():
    return False
  if runtime_state["shop_visited_this_turn"]:
    return False

  shop_priority = get_settings().get("shop_priority", [])
  if not shop_priority:
    return False
  if not _open_shop():
    return False
  runtime_state["shop_visited_this_turn"] = True
  info(f"Attempting to buy from shop. Current buy list: {buy_list}")
  if not buy_list:
    info("Buy list is empty, nothing to buy.")
    return False
  pyautogui.moveTo(constants.SCROLLING_SHOP_MOUSE_POS)
  for i in range(5):
    if state.stop_event.is_set():
      return False
    if i > 8:
      sleep(0.5)
    buy_item_icon = match_template("assets\\items\\make_a_new_track\\check_box.png", threshold=0.9, use_cache = False)

    if buy_item_icon:
        target_name, target_turns = buy_list[0]
        found = False
        scrolled_up = False
        for x, y, w, h in buy_item_icon:
            region = (x - 420, y - 40, w + 275, h + 5)
            screenshot = enhanced_screenshot(region)
            text = extract_text(screenshot)

            turn_region = (x-10, y-40, w-30, h-5)
            turn_img = enhanced_screenshot(turn_region)
            turns_number = extract_number(turn_img)
            info(f"Checking shop item: {text} with {turns_number} turns left against target {target_name} with {target_turns} turns left")
            if is_item_match(text, [target_name]) and turns_number == target_turns:
                    button_region = (x, y, w, h)

                    if is_btn_active(button_region):
                        info(f"Buying {text} with {turns_number} turns left")
                        found = True
                        scrolled_up = False
                        pyautogui.click(x=x + 5, y=y + 5, duration=0.15)
                        sleep(0.3)

                        
                        buy_list.pop(0)   # remove safely
                        break
                    else:
                        info(f"{text} found but cannot buy")
        if not found:
                  # Scroll up to find the item if it's not on the first page. This is needed for items that have a lot of turns left and are therefore further down the list.
                  drag_scroll(constants.SHOP_SCROLL_BOTTOM_MOUSE_POS, 450)
                  scrolled_up = True
                  sleep(0.5)
        if scrolled_up:
          drag_scroll(constants.SHOP_SCROLL_BOTTOM_MOUSE_POS, -450)
          sleep(0.3)
  _confirm_shop_purchase()
  # TODO: use the grilled carrots in the exchange confirmation screen
  # close out of exchange confirmation screen
  _close_shop()
  # back out of shop
  _close_shop()
  return True

def is_item_match(text: str, item_list: list, threshold: float = 0.8) -> bool:
  for item in item_list:
    # Use Levenshtein distance to allow for minor OCR errors and variations in item names
    similarity = Levenshtein.ratio(text.lower(), item.lower())
    if similarity >= threshold:
      return True
  return False
""" def maybe_buy_from_shop():
  if not is_enabled():
    return False
  if runtime_state["shop_visited_this_turn"]:
    return False

  shop_priority = get_settings().get("shop_priority", [])
  if not shop_priority:
    return False
  if not _open_shop():
    return False
  runtime_state["shop_visited_this_turn"] = True

  pyautogui.moveTo(constants.SCROLLING_SELECTION_MOUSE_POS)
  best_candidate = None
  max_pages = max(1, int(get_settings().get("shop_max_pages", 10)))
  for page_index in range(max_pages):
    if state.stop_event.is_set():
      _close_shop()
      return False
    if page_index > max_pages - 2:
      sleep(0.5)

    candidate = _find_best_shop_candidate_on_current_page(shop_priority)
    if candidate:
      best_candidate = candidate
      break

    if page_index < max_pages - 1:
      _scroll_shop("down")

  if not best_candidate:
    _close_shop()
    return False

  info(
    f"Buying Make A New Track shop item: {best_candidate['resolved_item_name']} "
    f"(turns left: {best_candidate['turns_left']})"
  )
  _click_box(best_candidate["checkbox"])
  if not _confirm_shop_purchase():
    warning("Could not find shop confirm button after selecting item checkbox.")
    _close_shop()
    return False
  sleep(0.3)
  register_purchase(best_candidate["item_name"])
  _close_shop()
  return True """

def is_summer_period(year_text):
  return "Jul" in year_text or "Aug" in year_text


def on_turn_start(year_text, turn):
  if not is_enabled():
    return
  turn_key = f"{year_text}|{turn}"
  if runtime_state["last_turn_key"] == turn_key:
    return
  runtime_state["last_turn_key"] = turn_key
  runtime_state["used_items_this_turn"] = set()
  runtime_state["shop_visited_this_turn"] = False
  if is_summer_period(year_text):
    runtime_state["summer_turn_counter"] += 1
  else:
    runtime_state["summer_turn_counter"] = 0


def has_rainbow(training_name, results):
  training_data = results.get(training_name, {})
  training_detail = training_data.get(training_name, {})
  friendship_levels = training_detail.get("friendship_levels", {})
  return friendship_levels.get("yellow", 0) + friendship_levels.get("max", 0) > 0


def should_use_bracelet(training_name, results):
  bracelet_name = BRACELET_BY_TRAINING.get(training_name)
  allowed_bracelets = set(get_settings().get("allowed_bracelets", []))
  return (
    bool(bracelet_name)
    and bracelet_name in allowed_bracelets
    and has_rainbow(training_name, results)
    and _has_item(bracelet_name)
  )


def maybe_use_bracelet(training_name, results):
  if not is_enabled():
    return False
  if "bracelet" in runtime_state["used_items_this_turn"]:
    return False
  if not should_use_bracelet(training_name, results):
    return False
  return _use_item(BRACELET_BY_TRAINING[training_name])


def maybe_use_g1_hammer():
  if not is_enabled():
    return False
  if "race_hammer" in runtime_state["used_items_this_turn"]:
    return False
  g1_matches = _find_template(os.path.join("assets", "ui", "g1_race.png"), threshold=0.88)
  if not g1_matches:
    return False
  if not _has_item("race_hammer"):
    return False
  info("G1 race detected, attempting to use hammer.")
  return _use_item("race_hammer")


def maybe_use_energy_item(energy_level, threshold_override=None):
  if not is_enabled():
    return False

  settings = get_settings()
  energy_items = settings.get("energy_items", ["small_energy", "medium_energy", "large_energy", "super_cupcake", "cupcake", "kale_juice"])
  if any(item_name in runtime_state["used_items_this_turn"] for item_name in energy_items):
    return False
  use_threshold = threshold_override if threshold_override is not None else settings.get("energy_item_use_threshold", 30)
  if energy_level >= use_threshold:
    return False

  for item_name in energy_items:
    if _use_item(item_name):
      return True
  return False


def maybe_use_condition_item(conditions):
  if not is_enabled() or not conditions:
    return False

  if "condition_item" in runtime_state["used_items_this_turn"]:
    return False

  for condition in conditions:
    item_name = CONDITION_ITEM_BY_NAME.get(condition)
    if item_name and _use_item(item_name):
      runtime_state["used_items_this_turn"].add("condition_item")
      return True

  if _use_item("all_cure"):
    runtime_state["used_items_this_turn"].add("condition_item")
    return True

  return False


def should_rest_instead_of_train(energy_level, results):
  if not is_enabled():
    return False

  settings = get_settings()
  if energy_level >= settings.get("rest_if_energy_below", 50):
    return False

  wit_data = results.get("wit", {})
  safe_wit = int(wit_data.get("failure", 100)) <= state.MAX_FAILURE
  enough_wit_support = wit_data.get("total_supports", 0) >= settings.get("wit_support_threshold", 2)
  return not (safe_wit and enough_wit_support)


def maybe_use_pre_training_item(year_text, energy_level, best_training, results):
  if not is_enabled():
    return False

  settings = get_settings()

  if not best_training:
    return False

  if maybe_use_energy_item(energy_level):
    return True

  if is_summer_period(year_text):
    cadence = max(1, settings.get("summer_megaphone_every", 2))
    if runtime_state["summer_turn_counter"] > 0 and runtime_state["summer_turn_counter"] % cadence == 0:
      if "megaphone" not in runtime_state["used_items_this_turn"] and _use_item("megaphone"):
        return True

  failure_rate = int(results.get(best_training, {}).get("failure", 100))
  if maybe_use_bracelet(best_training, results):
    return True

  if failure_rate > settings.get("failure_item_threshold", state.MAX_FAILURE):
    training_threshold = settings.get("energy_item_training_threshold", 50)
    if energy_level < training_threshold and maybe_use_energy_item(energy_level, threshold_override=training_threshold):
      return True
    if "fortune_charm" not in runtime_state["used_items_this_turn"] and _use_item("fortune_charm"):
      return True

  return False
