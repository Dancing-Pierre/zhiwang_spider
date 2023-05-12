import csv
import time
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.chrome.options import Options
from urllib.parse import urljoin


def open_page(driver, theme):
    # 打开页面
    driver.get("https://www.cnki.net")
    # 传入关键字
    WebDriverWait(driver, 100).until(
        EC.presence_of_element_located((By.XPATH, '''//*[@id="txt_SearchText"]'''))).send_keys(theme)
    # 点击搜索
    WebDriverWait(driver, 100).until(
        EC.presence_of_element_located((By.XPATH, "/html/body/div[2]/div[2]/div/div[1]/input[2]"))).click()
    time.sleep(3)

    # 点击切换到标准
    WebDriverWait(driver, 100).until(
        EC.presence_of_element_located((By.XPATH, "/html/body/div[3]/div[1]/div/ul/li[8]/a[1]"))).click()
    time.sleep(3)
    # 获取总文献数和页数
    res_unm = WebDriverWait(driver, 100).until(EC.presence_of_element_located(
        (By.XPATH, "/html/body/div[3]/div[2]/div[2]/div[2]/form/div/div[1]/div[1]/span[1]/em"))).text
    # 去除千分位里的逗号
    res_unm = int(res_unm.replace(",", ''))
    page_unm = int(res_unm / 20) + 1
    print(f"共找到 {res_unm} 条结果, {page_unm} 页。")
    return res_unm


def crawl(driver, papers_need, theme):
    # 赋值序号, 控制爬取的文章数量
    count = 1

    # 当爬取数量小于需求时，循环网页页码
    while count <= papers_need:
        # 等待加载完全，休眠3S
        time.sleep(3)

        title_list = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "fz14")))
        # 循环网页一页中的条目
        for i in range(len(title_list)):
            try:
                term = count % 20  # 本页的第几个条目
                title_xpath = f"/html/body/div[3]/div[2]/div[2]/div[2]/form/div/table/tbody/tr[{term}]/td[2]"
                standard_number_xpath = f"/html/body/div[3]/div[2]/div[2]/div[2]/form/div/table/tbody/tr[{term}]/td[3]"
                update_time_xpath = f"/html/body/div[3]/div[2]/div[2]/div[2]/form/div/table/tbody/tr[{term}]/td[4]"
                from_xpath = f"/html/body/div[3]/div[2]/div[2]/div[2]/form/div/table/tbody/tr[{term}]/td[5]"
                title = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, title_xpath))).text
                standard_number = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, standard_number_xpath))).text
                update_time = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, update_time_xpath))).text
                come_from = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, from_xpath))).text

                # 点击条目
                title_list[i].click()
                # 获取driver的句柄
                n = driver.window_handles
                # driver切换至最新生产的页面
                driver.switch_to.window(n[-1])
                time.sleep(3)
                # 开始获取页面信息
                title = WebDriverWait(driver, 10).until(EC.presence_of_element_located(
                    (By.XPATH, "/html/body/div[2]/div/div[1]/div[1]/div/div[2]/div[1]/h1"))).text

                # 详情源代码
                detail = driver.find_element_by_xpath('/html/body/div[2]/div/div[1]/div[1]/div/div[2]')
                # 获取该元素的所有子元素的HTML源代码
                all_detail = detail.get_attribute('innerHTML')

                url = driver.current_url

                # 写入文件
                res = f"{count}\t{title}\t{standard_number}\t{come_from}\t{update_time}\t{all_detail}\t{url}".replace(
                    "\n", "") + "\n"
                print(res)
                with open(f'CNKI_{theme}.csv', 'a', encoding='gbk') as f:
                    writer = csv.writer(f)
                    writer.writerow([count, title, standard_number, come_from, update_time, all_detail, url])
                    # f.write(res)

            except Exception as e:
                print(e)
                print(f" 第{count} 条爬取失败\n")
                # 跳过本条，接着下一个
                continue
            finally:
                # 如果有多个窗口，关闭第二个窗口， 切换回主页
                n2 = driver.window_handles
                if len(n2) > 1:
                    driver.close()
                    driver.switch_to.window(n2[0])
                # 计数,判断需求是否足够
                count += 1
                if count == papers_need: break

        # 切换到下一页
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//a[@id='PageNext']"))).click()


if __name__ == "__main__":
    # get直接返回，不再等待界面加载完成
    desired_capabilities = DesiredCapabilities.CHROME
    desired_capabilities["pageLoadStrategy"] = "none"

    # 设置谷歌驱动器的环境
    options = webdriver.ChromeOptions()
    # 设置chrome不加载图片，提高速度
    options.add_experimental_option("prefs", {"profile.managed_default_content_settings.images": 2})
    # # 设置不显示窗口
    # options.add_argument('--headless')
    # 创建一个谷歌驱动器
    driver = webdriver.Chrome(options=options)
    # 设置搜索主题
    theme = "压缩机"
    # 设置所需篇数
    papers_need = 10

    res_unm = int(open_page(driver, theme))
    # 判断所需是否大于总篇数
    papers_need = papers_need if (papers_need <= res_unm) else res_unm
    crawl(driver, papers_need, theme)

    # 关闭浏览器
    driver.close()
