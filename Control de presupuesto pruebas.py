import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import requests
from io import BytesIO
import io
import numpy as np
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode
from plotly import graph_objects as go
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs


st.set_page_config(
    page_title="Control de Presupuesto",
    page_icon="🚚", #buscar un icono
    layout="wide"   
)

logo_base64 = """
iVBORw0KGgoAAAANSUhEUgAAAY4AAABsCAYAAAB9/1VBAAAgAElEQVR4Ae1dCcw2SVFGlCgoiBcSPPHAFaJ44a0rISoqCt4S0QU1SrwWFRUURePBSoRVDIqoQUMUxAM0RjCoqFHBA5d4gBdChETEA/G+H+eZrWprerp7unp63nfe759Jvq/nnb6qnuquqj6m5za3Oa4mBADcGcD1AG4E8LTh/gUAbsH0ep08vxnA+zRVdGQ6EDgQOBA4ELhcBKj8xVDQSLRczPfOl4vAQfmBwIHAgcCBwCICVPRiLF7RYikSeTgK+ajFio8EBwIHAgcCBwKXhcAw7fRAmWZK6H78yqD89e8lqQQLz2g87nxZiBzUHggcCBwIHAgkEQBww/BnRxc0DN/FUUJJ2cuax4Mk7T8sGA5Gf1eSgOPhgcCBwIHAgcBlIBAZjFcCeETreoRMb3FEUrpedxnIHFQeCBwIHAgcCEwQAMBRgo4wqOwfNEmw4sdgQH64ZDmOtY4V4B5ZDwQOBA4ETo2AjAp0dxQNxiYL1rIWkrMfm9R5aiyP+g4EDgQOBK48AoMWf6xock5Jbaq8ZQtvznB805UH+2DwQOBA4EDgkhGQUQZf0uPi9SNOxQsAGqjU1W1a7FS8HPUcCBwIHAhcMwjIricueH8TDcgpGZc6U4Zj09HOKXk86joQOBA4ELhoBAC8I4CPBfAwAI8G8BgAXwbgc+X9jA88JYM5w3FKGo66DgQOBA4EDgQMAgA+EcC3AnjuYCD+LuXaJ579PYCnA3iAKWqTW9m5FZPwkk0qOwo9EDgQOBA4EEgjAOBtxFi8NtbIDb9fD+AmAHdJ17bu6bDG8dAETT+8rtQj94HAgcCBwIFANQIAHgXgnxLKuMej7wXwdtXEVCTMTFUdC+MV2DGJ7EzjG/08ZZhbqPUvJW89kfjZQyR3z11fWc3Jk5E2oVFPVybtqetieDo5iEeFmyAgG4nYPvl32ccjAfgY87JeqoP1esYRyBf0kogcQxLT1lUYImAei7Knv/dowVA2MtBQ6Hs2MXYtv6mcz7oZQTojj+GPj99v4Yd5aBxvaMH4HHkiZaRKKRV27Rs1vEqbS9HS89nmm3IAfEhBB7zbEhYiI/Y7vrzMzUT84/3lvToA4I4AntXau1bkez6Ad1gCeyl+EGR8/MhzlvLUxJM2AN8DgIZuj5dry7Mc+0JluOXFTrF5B7byWzgwswevPPngRlvnXu5Fpl5DeRIDL0qSDkVupNdDNrky2A45guZhqqsMJYA7APhaAC/PVSbPi86w4KHHLQWDybYko/7LOV8PwHsC+LMFQLaM5iL6ql1YCeIeurZjA7gPgL9JlL2nR9fV8Ckekle5rOGTimK1DJZ4E6Wpx9msobc2LzHcxQfDxINvHTGeQjY8augcBiMlS9JBA+Z2aAC8LYDfSxWaeHa3UpsVB5ffHOLFw13p8DIkfXzO2YzNZVOisSpuGGXcEwAV97mvfwXw0VVER4kSO6r+IUri/gngfgD+5dygLNT/iiXGxMPZeoRRInOTTiAdrFVpluitjduEryV5arwYjTWOwKbTIpnNKrXYbpnO5dDIjMNfVBJU3MUphmGcCZHywqhPjIfG7XtTjxiNvXgEKpvP0M5RGw7KMT7ocNVwTzyMPRhTxSQXPrmEkRjUPci3m4cuCpPTD3u4zmY8ZO1lDQabGQ4x6mtoO0XeRR0B4A0dIw3S/LiF/jiuZzCNMGgNB0ceo8HY9VoHgLcA8JenkJCzjv8E8L4lAcRxieGwezhqywTw006az5U8+37MgAkXiPdyvcDi23ovHtsaL3sLPELnb+XLm08WU9fysqXhOOXU4RocirsuG3D+yJIsZefn2F6EaE6dcVciR840HOM6jKR701JZZ4sD8MtrEN8476sAvGUNOIkh8aph3uDJ3Xtj3noWf/sURjKX27OeHmWtUrAJOfegqUcZHNGtWnhNyTD3TEZcPUaRmxiOHcspJeviVC+Av01lyjx7fU5m+lwMwoi7lDHupJJpqqfZdHq/q1COCMnwv5vHvwrgDZaAS2wnXTvaeOJuECgT8rwUNoNi4ZcU93g173LbqSG0GC9Oe6Rk1fKswxSV0r2V4Yh3N2p9ew2T042JddMl+p+1JM/cGoesQ7J8HY0095UlGprjhfglEPYS/yUlRhNzqatGG6wLwJ/uhfkFOmZbQ3fu7TV9jfECjIaKafNRR6K9a90tYXflJKOhFlrOmSepMwD8oJOoh5V0lcbJlJTuqgqjcFmn5ZQVd1W5tthr2ZuGw8GEL3QCcs7kPBPrDjlABiP4HEMcj3Ff1XkB3N2Ut/fbe1hcOjkExJAeY/zXC4vqRXJRQufcDebleRMPPpJxz7WDX7Fl97jfueOSk+ctKd4BeI9ZeutUOfEz6afcfsvLGo53lmfd5RLT4P4N4BOEuEsKkh3SDO+Ul2Q6D0jDtuQv18J2Hr7a8iVKtlWp0PjynK+i0ZUGz+PyaVxar2pPquOb32oMySfpt398lvuOi5fHpAKyclpzL3R7aSql766gxGsu1bnLuFguDU7Yi+MySr+lfLY7Lo7z5UT+8Z7tsdgPS+VuFjcYjt/ZpeTKRPH9jreKQYnWNiiE1YDLyb9laqaxsWd+qt+PtHg0KhV6PcHjseWV7sVIxdufp6jkf1UZ9w7TU2wPpLG4a0b5FCeEa0NrjCK5XrW+pvTEodDXY0HcSmYLw+GlcW1/Uc/d8uW+T+D9dc5CvjUuo+a3rKPQkeE23U3aTg0dxTQA7usEY0/Jv8YyR4UXEedWgLY83gO43bBp4D+icks/XxqXcY7fjUolOa/roV+8oxI+qbhFwzEYpjWL+1T87IhNToRguUYZVRkqD85MGzlJKVxbnnU1HA1eevFluVqMRGaUebPRj+sC8OtOQD80LuPK/AbwDCcYe0r+MiuIqCOtVoIsu2Ea7wmWpnPdDx3H6/33wuvODQ2kaDhWzpFzmN/Fa5PtkQ3s9T+krmF3Ty3dXafWGka9XXeiieFqMh627wK4E4D/rQWRBsvmv1L3wzc13ggAp3wu+RrPspJhnfLRZYqKwh6+PfJkLbQyvN+5G4l4W5Xkjsl6e5lU1p4razik43unOrTu5JbKVvk0eM9KR5a/FlpkWtCzduUarbXQlMvTsCZVvVEiV2f8vMF4jXKz5QD4TBVmZfgMm/9K3fMLfJUg7DnZE6QjWeWyeopKBT0c8f5qB/M8w+q2mvdcYWREa8jv2lkbRghZBd+geMgvPcxubcDKsWEkR3p6G2aPIeB6gWsUaPldc++tdysvvYGOmcyGnZU/UtORTJrPWYPdrvMOR6ZT6V7yRUV9XdSZuw115XRgDz7d98C3NKDhZFiPN9plTtnS2TDiSSr5Rk+RRqOrIYx40732nnbRzXA0jHrGaToPsZbfNfcNDkSX6dIUzR7+Je1klOjchsspraptuClad/8MwG83ALqnLJ8azfV2VYLDlw6/ysnsF55b6A2KpXorrIe3wcur9opT5TbwoaLaZCHa0tiwVben4fCc/BuUn4JTE1pe19xHDl1N1dmR5xo6mLem8ihNaEfyGYUouvjzt9fSu+v8AP6ryP6+I39IhqA6RUVPs8siqAoNwC85ISieua/lbhl6FLbwlvT2e9AoI4alhclXpuqKNjrUimEzxWNpbBgJdRkFO6cgJ+t8tQAyneV1zX3ikNElMpp2vdXQuFRxIj7QMsTxwEHPFQx2DW0XlQbAXT1I7CwtPy71xtH5PF0VIIDbA/hvB99/sIcG0LAmEDyrPdBPGhqmOCimzaY5UrgMIyLPBoDViiRykmqa5cSI1mQwaVY7YA0jxq6zBVZmiW36htXk7YQWAC9Kpso/XPXxOUv77u6Hl9o+KM/3rmO4C4wfmeJbzXqt7pixgKIpMK2nFD4+LuMcv0sEZuJOqnBrMHGu0ZCtiXddU0ePNKKQ7BvnufvVTo1z2mc2NZaRfe5xD3qJhefq3odVxg2j8DB9e2zDVRQlbLDCnkawZdovFG9Gp6g2UXwAnupkYnVni0Tk/rlCphPv1F1xxwzO6RgV0e5GTR0h4QgsfrFV+c6Fs80BuYSZ56vbcsPId0ZzLwwbHJEw4gLwkAxGucdP70X3LstpaIw5oE75fBSKaZSTIWVPoC90Gy6/5dx6PbYnfq1lNXTyXexka+W3Jp9p7zWyTa6n1GQ0aVYZDq41mrJqbjd7Wa5Bz00cUQA/VsOASfPgGplebBoAH26YvYTbXyfY5ryicXqCXwUE8Kieghi+9PfeTkB+qmf9rWU1LNrGbHIb7w2cT2+lYU2+aPoxpi33O3iHa+rea16nTLkRISm7HHiZ52sNh51GzlQxeTxR1j1l0bDJYjLykXeCJsQWfnAb7p160n/2sji9Y4kA8F4FAPYWRYXGl5i0QY579eW4c36N6+stb2vvaYicAHz+2jp75HcqmRKLnAbUEzqTiqgHvXEZDaONzRROTNs5fovnrlOyJXlpXJibj+nVBJXhWsPh2ThAkjaZKm2Y9pyMXgF8aCVemuw3Y9wv+rcAOFl8Gj5I8vbK7c7Df5YX8fTFKzUadwHwF0L77ONFawQ2HPzIrwx6ru8VpZ1bHG19/tkePho6Si2P/P4FRyKbefcNmxFI+2b0eHDfKm20a3BJVsVp26XMUXzWANXwuodtuMbJjFjL/qRembQnAN+STZ2OeEwNPheRxgA4m/tM8767p/xWCEcb6nlxofCOAH7fUPrAXsKQXRSebbiGjO633+jhq2E+t4Vgjv5ujDuZh85U2qG8sxzKmKJlD88aDGlxlOAU9MTJ9ODR0AaLBs9Tt6aV9ulkef51PQAvdhby/krDRYfGaJD/2XBw2DHw505gTp38a8Ro3CIVc6rqTRJfK7xXL0EB+PRTM1mo7wM8fFGZF8raIkpHIqums0TGXvomU68enPaeVvDwHBuzOGXnBHeN4ag+MUBoWjW6UVkKZhwVe3BTWGb48cgQjawMX6u0XHQYeSwzYMjcsLD8M5WgnCPZE4VG/UzoaPgA/GxMTE9BmcX3uJpT/y42RHaUFN/OxbyePNG4N41EGqbYkm+bp/C4xGfOtarZFEuKZ6eg1xgOdfJqq+RaGt/Mbv1jfs8xLDFd/M7KrC8BeFiccOH301K4X9Sz6D2H7MtRw5Hq9Oj3eD2VgBslrkYjtTXuRT2FA+CvdgLID+X4Gho6vbrJfKymbZjy2YJdKoFZZ1Qa49C53ZT0rvZSSd+gcK7f8K9pRNTwxnWVkncKuarMhBxPPeJ1sjVLnjQa5AvAT8xSlx98RozHRf2OjAZZzTbgwXt/vzIWZ4n9URGc7qBSo/E9GWrGkUkPIe0Mj/vGPImy446VkkzZeemFnvvimtSiARGevLQmjWaMV+n3UK93SsVL42SHTokWG+f0nqtHXk7iZ+uhlsbcfTQ17qzy5MlLRuO2AHjydu3FNdHL3YYrndAOFRc9BwB/XYvOCdI9l43SNEA1Gt9YqPsjcg3Z+3w4m+oxhXpOGfXCmHZxCLiAvOjJG/xOSXOuLrbHLM0NtHZZTG0Y5eT4yz0f224sx9LvBiyKC+K2rhyRmeezI0tsWbn7oY16t+Fmqt/8cdEwAvhIJwW/lsNk988TRqOqgwG42QnSVsn5Pd87mM6jRuNLCxW+oqdgAPxGoa5TRt3b8iU7VcYP8tjnpXvBcQ8jD+KW/Rxpg7JZdIZKuDDuRJsIXKMi6b+6c7CmrblGNDUFmjSthsNDv6nuZLfsQ9nRurabYQPOTU6KHq15Ly406wHK8yJA0onuoxnOGPL0yTcTr5qNT43GVy/Q9A29BAXgLRfqOlX0wyxPYgCSmxtsutS94Mkh+R6upMI326xraaz2slOY8JlxTmrr9KarctosfYPh8E6deQ2Thwe34WjYhuuhZ21ajtSr20201b+m7omjZ+W66/vELoxkJ80xAeA3a9DZKM0Lh1HPm4uS40L+KODh2PTHVdR31xxP3ucAHlxR35ZJ/gDAZB+4OANNRsPyLzvs6G2d86JDMFF2LcrG8tV6f4INBMWpkJjuBhxc/Zv1OQXfYji8hs9J0qrk3HVV60jfzVlTcfdjLOvd/E54T9ULZsoEgI9zgtUrOQX6psZojMIFwDexl65xEV15WBsCePpShRvF89sij7T0y7QFsXHPk9ty4nuZouFb7DTQ57gmu6ESDs8STW6FFmPA34Oi3tqIVnu3Qo9dl1zCILtLMsWrPnPy7Ma58f2JJV57xy/2JwA8fdtz/aBifDGhKNx4XtHVaJXZhq/decBNpf1J1p0wGqktt6n8d1fae4QAeOZV7fUq8RL5FnvrHw+ZvGNMu8FjsZHHeT2/xYg8YqjvlAuak7UOpzKjbFyefA6Phnpr2wXTuU56bXiHpekIeSfPrrVDaUsejM6ZtjjycB7zQj4+JdfOdvlcvNL4LUnXgpllTITPjySd4rqZdYuSpPc3TmEMZ1L9eGXlXRSI8t/wUavv17w9Q3mBjgvaxcbds04tS0auNCKbLqhrfQwb1jealKatU+rd0lhWTy1Kn4sdv1IXcI8ElHen4XB9PrbB+JV43DouqyMBtGzDvb1ifBFhxjJO5pC9jAwvv33R1lLj9ATpMvPufBHrDYejzH+6sm4ebHgHL2+l9AC+ubJuTdbtbCzBghjwDVguZK+SYYnP2rhByXAUxQXF7kZEaRClqXjWhk2jaa1TQ+Gvtk5vuuqRYqYPl+prdig2NhxbGuISHk1x2g7iEMD9nAW+IC5j178zc8PuBbMUkwB+0gmeJ/kXsU7xbsM7Cc7pkvuk6F7zDMDvOJjgyz7dvAxRoJzjZufLvu+whr81eUVW3dYElJZG5d2sOLVeDcUwOsRenbRKhg38rxplb2w4qsGRhGxPrX89nJlkOxqmjp/gZOSrtT3tPsw0OIJZ1WCXGJSTZ1/qBLAm+QNYtyiisRMAeCvnEeaj4VniwRPfcJjZ8z3ll9LKqItTFauUQqmOXnHS7lZv7VV6Ms5PsR1p3l6h8EQHpqTEPDxXbcPNTDMXeZf3rVrPc2K+eFq7WF8txtKGi2VFkc3TbUqTOFuUW+uVHLkCeJmzwG6Hqypvm4SFBtdltKFEDzuM3hXA3ztBzCXnq/v3Z9lDAjbgcSgv6xuvzmVKPN9k94J8ZyJRXfbRVyhOa0Lz4mX11Maa+nrlbVH4Fkmlo6UczXvK0DkyqeqHLbxbDE9xX4sxnR4nPZOddbX1pNKtWFuZGQ4A3m24r07RtMtnmTnRbqMNyzSADwDwj85GESd/DYBxakka2CgwAJ8dJ1z4vdkH4AE8c6HuOPoeFifvvZmaotySQ2ZvmadOL6PGGJea32GruHN6ciz7DHx6D+1blKfIvwarc6dZ5IXy8I5kyH8vOa7AcjY7A+CLnYA/pRcfm5ZTsK5VXk4LcTIq+BsnoJqcL7S9rYyS6JWMDbHyHQ0tg+GTWmivzeNcAH55bbmpdKJwOTW1i0XwFI21zxq95rCjRaaHrJwX72tp65Uu46jl6Kzahus8xDBX1ymez7zyGNcGxR0ch7is1t8tQKTqGhzln3OW9Umpcnb1TASU2ra3yWjDMg/g7YYXBH/LCSqnoLh+QY+NRoO7ht4JwO86yvm34UNTD7G09L4HwHcpPFeTERP+uWuKV9gU0MKP8xjwKq+xkQ7K1HuFaYoWw8H21EJrS56GufvFbbgNZXrx7Zm+xnDwPSDP1X0tz1O5pJ2tsQC4HYD/cJTVdYNMS/usylPwUhYba1UFFYmcHiaPC6FiGUdDAD4fwD85BPPzAN6lgqxVSQB8u4MmJh3XajyVyqhN3wxetZ4hhthD8qyTeGhfStug/IPib8hLvheV2RLNNfHSdlOOWgn7omwbyyzVt3XcItYN041d3sOxMmwAYaYz2a+d5XTbIGN56XpfmKIir6Ejdq00UxiVOYBnVIDM74HfBcAHF4xeqhh+yrbrOxIZVsbHMmWUoiP1jB7J7UrlxXFDIdwMwKvLekaDx7q14fDs1JnsOGo0HN091lhm/J04MFTEWAxm8+a27MFweBeRi5WdILLGcLjIsHj0uncRcGviMOpVGjgd7iznKzXvLkPxMHOez6ZKoQQIgLcfPlzyROcooiQbHuHx5aU6e8c1bMP9uVoaRG46yuBWz6JScZTLc6Y812ZtpGH0M/HIGw3H5MiSWtw86RYctRz2E6MY1yejzlzevT4vjg4anJiwvhXj0/q7EdfZ9C2AlzuFcF0rzSfJt7A4N+mIJyEoqkQOKOT3Mn4KwF86wf9D8ezO8slFmT7zkPzFEfvJn3JsiBr7rh7yoKy9e9e3NBxeIzYxno2Gg/LabJS9YrdYcYPKCT4a5WnHtWmXePK2xZmnn+xAjocN8pptYADw7rWASLp9b8PlfG6BoRkADrw3SyoL4h8P4FGyJkLlYv++DMCH9XzzupUZMXYFiGdRdyvVJR44T7Tlxamp7oa9Qdm6Dqsr8WfjGubrZ97miqmbTY55aFBCIuoxmHmxilfjCMaWfa77JcPhmaYkD90NfkMbmjlS4uh5MH6yynaX4cL+6FlH3CUTOyWq4TCzl5ZYkWG7jjI222rbYDjYIYpTDiW+cnELI+FUJ5wp1pUKtStPDcrD8pjdYtpgYG25577PGo6GKaIsRrk2VvO8YSQ34wnALziB/oQa2s6SpmIHU3dv9iyMnqnS4ZiT+zoby3emSI1GGSyy69RUXGej4eBay2SaKC7X87th4Xi2i4X1LYyol8RDI724eLvEV0J+S/Wm4pP8CY/e6RwuoLce07+Uz3N0CvmcKVnFs8Hod+8XYpRT8ig9m7QZznw4t+G6N8goZpuHlV5KN0WwOUM7rGA4XffxpdaViHtWNOXG6bfnAeC7Jrz+Xd5At9NyPe4/zcLXaDhIH98hWdVmpF0++1Z2q/9zyi47RSFTetWFJRLeaPGpvReDwR1vOkpMFF39KDn6aTCMTR9ocvDMTRqeq2Q4vGUlMaqlPZWuYXF+dlQ8gE/0AMI+n6JlF88qRhuzebpdEH5BRADgwvwlXJNtfysMB3nlyMO91VkMRquSzSofNpeG9wBSMuNc+40lAyV18b2iBzaMmFJ12mdJg7ww1Wzz6/2mswgNbSc5kpL2oDTXhJusxw7y9o7mZnqz4RSLk+78rFap4gkteUHdh33VBF6BhA2HmdV0jq3SvKeFvMKpqKGDivZmOdzx+ngkIvPXfE5j4R1h2Po5NZJUqsrTygVpW5fekzduUOCf0s973Rqt6XqFM2VE3hrklCxHceoRNhiOJE0Nnv4m67ENhnnmxADwHLLKNrP5S8lNsq5scJt6Jk2EX1AmAA/vpTU2LudVMawNnXZjErPFVx+FMxiPc33/PEu8I2K2xbTS+YurmMy9x3Lv8buj4fB6+t31lWAcY7j0e4IxgHsuZYji/6yHHLqXIUPApdEGeZntUOlOzBUuEMDPRg1irz+/LxZDwzTBuXirbqMNC63n4ilV74xP50kJLDM5JRTLfu3vjoZjD9twH5oSRuHZbLoMwCML6VNR371WBpvkrxxtzBZ4NiHmihYqh5nx+yCXcCVP36Si2Tnxbg9zZ6MOTrHVYDzbYtowIixuHujZDXsYjoZtuMU36lv5q5SP7Saz6TIAv2wTVNx/bCu9m+arnLObNdZNibpihQP4mIoGsock2dM3h07j/UbEqfhpfulxUGqll11PRT/rGddlKpXsZKQgo0GvNz6bd9+qy1XyZLGerXE0jA43WY9tWLOaTCnKNlz2sdprn9twHZ7KTJhbNbSrWK756l5tgzlXul8s4V87Oj0h8TQas2mbEg9x3KB4z30IIEcZ42J+pZKdbDFtoH/T7bcJfLk93HUlyvBuw52sK8Tltf52MXFr4gkdAD7ZWUb1OXWtPDXlGzrdcyoZOQxHE8K3ZgLwJ5U4nzvZVy2xWancTsEHvfTsuxpLfNj4himIXvxNPP9KbMOOsYYpHNLtntKzWHnvW5wNW4eMqDx4z9YVbHmt94Ns3KPTuK7hG0M/4GGEXweMyzj7b6dADsPRKDEAd3c2lnMmv+cSm9JuqLTPdTVPTZV4O7HxoNc/8UZJW4WSnfTDhgXxSf4SHr3iKniatSNbd8PW6dm6gi2v9b6T4XjtjNnyg+I5da28rMrnFMjJG9wq5naUGQAPWLyEa7YNNwejGI+ahdyefNNgcNojeNw5+lqfS/msZ8tr/DJlisaKdaQwZ+7sv8rPzFil6Oj5rIPh8LazTUZUHfi4twqhMnxZTzl0K8sxTUU+D8PRiDyA51Y2lHMne4qXRfHCtn4fgqMbboPczGBYvkV5107hemRGBbg4tSbrjjnjNeYXw12zhd7SN1lUtzxved9B4Xr5XMS4hd9GQx3Wo4azqR5thVFx/4QWOjfP4zwv5zAcDRIRJfTiTCOhQrxJOlaP86XWltG8yCwGhIqxhxGh0uRiKL8rvYkSqBGlyI6jgzU8KR9uoyeY0mAGuSrdEhee2zSF+7Ng2UKr4XP8DHSBpxiDMCLTMnqF0h7i+pZ+h9EPgM9y8MFy79WL9m7ltCyqdav8GihIGhkP+EtdyfntqwKLtK0HSSehMaHy1D/yToOpvxlSObOjMM9ZlNsS9iJPVeKWdvJi+SG/5OXkU0JLPBzxBwKrEWjYF00FuMtOvRqMjgUsGAxiSKXi9j47kngUdSBwIHAg0IaAKLCUN1x6Fubr2mq9urkqDAa91MPwXt0mcHB2IHD1EZCpgpKRSMVt8jbmJaNdYTA4NXMY3EsW8kH7gcCBwK0INLw6T0Nyy4FfwI8vA+l3vlNGdtw6euB1IHAgcCBwZRBIabrKZ9f0ot9gPPlBnpLBIIzcynlMS12Z3nIwciBwIDAiUGkkUslecK1BKHvm+aW3pYPkuI5xTRvWa61tHPweCFxTCKQsguPZNeFNm/WLpReQuI4R9mtfUw3pYPZA4EDg2kHAYSRSSZ99lZGST5suTUcRl2Md4yo3hIO3A4EDgSkCK9+GpdK8Uh62vFGHOMEAAA1tSURBVLTG72EvjS7UkB7vY0yb1PHrQOBA4Koj0LgdV5UmQyrYi56yMmsXt1jGFu6rzhu66u3n4O9A4EDgGkRgUPpUgGsvTudc1FvQYixuAPBsJ/OHwbgG+8nB8oHAgYBBgFNNTsWZS05vfdfGY4WxIM+7MRjytv9jB6L4N5sqFJlq/GONuMOtTMkxDafl+MfdYjP5mbqyLy/K2VIsi4cRvpHk4RTe/bXCUjmy+WCkV9Pb0MSTTuVrcZRr8jFPcpeboZ1pJoc7mvwWo2S9LF9ps7TrveE/0BHLSfOLLK7XvDWh4UMxuiGVz0FnkHeBTm5Jn+FheFVZaXh93MYAvINpL++VoZltiWXM2jrTW55ycrblGqx4hhzLDTKJ0lE3Jus1bYPxMwyELp65xvhSHWw35C9MeUf8pPqk0hVkZOk+yb0AMPDW5eI21aQQTsJMohJRkFSK3pGFArIbg0H2hB+ljeHktGIxjjZ+8hU0kXduwZ/TjpPOOXQyHtzHa1KPQi3l6XoQG//7SHoGDxea7TfKX6F5NZROw/QxrTwRtSS3m7WMXDjww51uvFL1WlpfomUIhqV6JxgxH/GRel6p5WgYYRLySvpSwP40Uxxaroam7rgs5o+NoR4TP8GaZUW6IHyRUDZ/xGXb35Yni6lNo/dsK4EmAJ+nEQDeX3myoeGPeSd4iKy0/XGTyiQ+Koe05bbSz2ZNDN+zD0KJk6SkB360vogupgt4ahqGAJ4phfwrgNvKM/sJ49kpv1opabBlnfzeKAdD06pbWvKkFd6aOWn8nIIiDblGssQcGyCFdxYeShiJ92fpnyh0o4Q1TYhPNGYqOyp7VSaaJxj/AQOdynxdii4TTwVNRf9wLQTABzOPeHjm8fToFaMYQgeVsuyak9JKetUYsMxi54k6ePDQovIp71HW0XOWT8OZwiiUJTyyDF6BB8UromFUMlSekp6BPVWXfKqxZlzx2xkDvVbJ6OnCDJWeySkPBrvQLgyd9JD1GtsAcdEHCTo1Kij0iFfyon+Wp/AOGIDvk0L+E8DtlBYbDmXYT7VOFHDUdkO7tfl5L2WogWGVpIdt27alcJRSxPekTilP+8XMAEu8lQvrm+Et6f5Y+A/xgpk8njo8UbvJ8suyN78SykiJXhtSeT9wSwaGt7c5/OWIgnVZRdNCOxsRlUTWa9mSl5qypbGTN3bIMdR8ovS0c2hHDY3e5GG+4CUyf9Qgg/KLDNEElyjPWB6Ap9xKFuhB3V7KJqb2CuVLvCo5S6saM8ZNlLTkUf5nIwnG6yWYaPlWYdmOHcqPFFEKIy0r1BspmZkhMzKDoctOEc8UgDEeQaFoXhuadBMDE/VpNVY07HoFrLU8a4TMsyydUR1qaFShBl5NWSrTEAfgd4WgF2q6VGj4tLhzalSvGT9ajrQBdSIpvwnekczHNs42pwXH6VnuwLsanJl8ovag6QLdhq63AfA/Us9N5rmperwN9FrMNf1ZQwNETHSP31RmHPpTwc/mOZcYF8EzH0cSnC/sYSQsX1SyEyWxRNO54k0H0g4aGqRR8lSqajhGpRh1hGQnyyg46+2FBkz+jSEK0zPDusaLBNgXKUYmnSpdJlEP33q0qnxsnTNFLHXTY6dBovKYGDStV0OrEKVTW6UQFG5kCMNzLUfqtQZHecgqV8mjsghKxtJky9d70x9DHo2zoUlHxRhw4D0VnvypMrS4BmOp5Rk52Wm7wK+m0zAaXahxmvFq0qvhGL10jjAAcKTB60maLhWyf0o6Bryn/IOTlMqjzyI6Z/1cyiKfbE8qU+vsBFxZpmCr5Mz6kjFE7IcBc6VHQ64BaiH8uJOUbUeiGh3aomk3QUZa3lnCCFwleOuQIwTOLeb+tGFsRQcb8kQZngV8R6UGiOBtMbs0ZsXLKkZVGmpoqLwnHUGrN4aH1Wi+pJdqO4RiyBEGMI40mD98fnZoW2owghJiXUJ3kValbU0oxkKhIw6KE5VcwGJIpxgx7ahA4nojjNTQBb7i9PytFQ912akQHTFNFIDQSsdIr5lisnWwTE0ofJUWa60ynPFnyrGKKkenVdxhusaUEXgVDKziH8sH8IEm/UMsX6l7YySpL5Qutq0ZLza/caKCg2PjU/emfLYVXeDW0MpnYoCjfkGMrCGY6BoAjzL8q8GyOFl5aX9UvoOMUvSf9JkB2PBz5W51OqrY2E4KfGVlUaMMCp3ZjUKjMlRlHDqKUd6TaSJbtSkjTCVI2ar4Q2M1bSV4xFzTMK1Fp64mIwqjnMeRklF8KVpDfYZH7bwazjxIy5Pem3oNif+/SCvl67RC4Enza2gxUoVllMzECEiZweOkXEw5lo7c/cSwaV4b0vAZD9eWQ+UWjKLQoh5/wFrLihRcGOWZAqlA1cHTaR+N1lGt5ZVpNL0aaqYPih7Al2gBAO6htOTCCHvNGjAt5NO0E2OWS8/nmqEinOgR0y9CXaaMSVs1C+OvUVpMO6Xsbd8ZZWLKCjLSvGcLpfGokjA0XolbdprFRnY28CsqNqPCUbEZqVB5aOekx6KeSjASJm3WgzWNPniQJMsoRq3XekVhR0m0MH6d5LVpSadVLjRw6kEVaRUFadgIt1l+LKSRYmTmWccLJZqRgS1D+FHlG4yryTcxdJJeZcFk6lVaDEz2cMs6ZvTFtNjfgqtiqQXFC+PatwPWWkY0FaTTTtZb1jJtyPICnaZ92jT2noY5eN1GSb5e6SiF0gaUB5Y7wzvOHynflrZCWVCG9k8djIkBNhiSxmC0zUhpUr95/jyl2/TBkTfjFNAQ23YT+p3mPWtomLcCv9T7ix1dpBqB6WjaqFQuqpzGhmyUcWiompAdIFO29W6Ct8S0xhCNytI0+EnHNfSlthaGTmbyByUcKSAlN9AqCkA7r52eqXYGhjpU6SRHFFppAaMwyiOvgo1VrhOPUuKVR8t/mGakQTPlKH0T/Blfe4mBpLeql44GrHwDrlqukV1wGiJDQAeAiiv8aV4NjZIjHyGd3M8UHYA/EiKfr2UshUNZahzZt4NyzuUTPBSLGd/MJ/SFkUOkA4Oh0zpMOwoGWIyaOm92tMVRlz4P7W6Yyr2rEmXbm3mmI3adPWCUtqXgtChNuwijBmN4uYhbNigqlllD3QW4K4gwCnf08ow0tGFqY9Oo0OhNYw87iywppkMy7wS7qCPpOgCVQ+hsLGtY4CttLQxGJtO+UrSGPBGt1vOa0GDT2XsxPIpLToGoJznx1LUc23GpbPhclI6WG3iQuJmhkeeK4UQBRDhPylIaNLTGPFagKV4jOmfG1rQPqwyTdCoNcWjaZ1CQcRr9LethuqPo2/T5UpiisyKPymfWniLMtf8ExyQuO4Ut00Ty0Pri0G5ksQvj44uykYxCHzS4anmL+MZ0n+x3JRDKyLnDK2ssVODi0SjOqrT0N0MdbVilGjyySOndGJVrF/tm3m7UoLXOifKNFEFqa6Gd0qBCVe96LE/pYTh0zqCw2LGjOHr49OJ4Be/Ypkndc5pS8jBIKuWo3vByoWCfxChSJE+zdUflWUWgI4KZAjC4JA28lh/JZHI6wFCGHdEEXg3/k1OtIzpt+iydSoeGUfuctA1NY8NBhtwlqVfVlv0I68U6tL4BKx2lsL5gNAVDdbrsiFDTp9asZu1I6NJyUlNbs5FCpF/vSlqt3JR2ea4zCorXrI/a9Ge/F0AURCV6LyHpIqChQ54dsA0JsIpCq4kEod6SNrJJoxdZWmXNhq4KWIuiwg7GRuthqAkkZDmTdJa+zNbCoJCkPGscamnVzqnkBO/Y0pq6jzrqhHZNL8pvCSO2u0n+yCgrrpbW0NGlDqV/pvyG+ODtUmZKWyo08+EsT+u1C9cTfIbyLOaa3tI58ciVSNKUqt8+i+QflLNNY+8BPNKUn7v9jijPTGnb+Nx9RBvrIkYWJ8o86BFDzIzvVDsyuM76BWmK6h/rGTaSPE/qsQZL5TNxKKTvGrKmzlSO77M/F29NvQ/LwCnvOaogsGw8k457doBOQIBpsEHJGsURGuzQSNXQT5QASWTnMHms7IjtTIlZtqJ8YfSgaZa2Fmo6DYUWpSFHq/Ki6TRkW5zRoGWnQoNL6KiZdFwLSNVLjJMYiTEIXqUSKaOHSZ5IicwUbKQkZrhYmiVtilaSwL4y6SdCpyonQ+Y4+psoyYjOyajP0qD3pn2y3Em9msaGAH7cEpC5/8woTzCq9nnNvUxJUYbxRfys0bAj9hnfpm2kRvjJNim4a72jzIeNJK+RB89U+s2U1EQWjB9otO0r0Kt5dx1KZ6fwUgJQYHqFFCjroqEoel67Bq0TcaIk2KhDoxF55J5lMZN8xJV/k5FAjlxTVzI9t1OKsgnxhubwzJav6UvyNfXq4myWL1t2fG/KCfjFaexvk74FozFPSoFaTFLxpMHgUksrjR3bQRVGhoZVdGbwSsraphUe38/wSdpTf3ey+YxMquqwefV+CSdR8krLzAAaGkbZGCyLNBn+KKvbmt/vEtHGumdtvLYeLWu3oTDOuVR6MK2jERogGgidF2TDr+osuwXmIOxA4EDgQOBAoB4B2WJGi6p/nBqhBb3OPBvj6ks9Uh4IHAgcCBwI7AmB/wNTGaUfIJ1eQwAAAABJRU5ErkJggg==
"""

st.markdown(
    f"""
    <div style="text-align: center;">
        <img src="data:image/png;base64,{logo_base64}" alt="Logo de la Empresa" width="300">
    </div>
    """,
    unsafe_allow_html=True,
)

def init_session_state():
    defaults = {
        "logged_in": False,
        "username": "",
        "rol": "",
        "proyectos": [],
        "cecos": [],
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def ct(texto):
    st.markdown(f"<h1 style='text-align: center;'>{texto}</h1>", unsafe_allow_html=True)


base_ppt = st.secrets["urls"]["presupuesto"]
Usuarios_url = st.secrets["urls"]["usuarios"]
basereal = st.secrets["urls"]["base_2025"]
mapeo_ppt_url = st.secrets["urls"]["mapeo"]
proyectos_url = st.secrets["urls"]["proyectos"]
cecos_url = st.secrets["urls"]["cecos"]


meses = ["ene.", "feb.", "mar.", "abr.", "may.", "jun.", "jul.", "ago.", "sep.", "oct.", "nov.", "dic."]

@st.cache_data
def cargar_datos(url):
    response = requests.get(url)
    response.raise_for_status()
    archivo_excel = BytesIO(response.content)
    return pd.read_excel(archivo_excel, engine="openpyxl")

def validar_credenciales(df, username, password):
    usuario_row = df[(df["usuario"] == username) & (df["contraseña"] == password)]
    if not usuario_row.empty:
        fila = usuario_row.iloc[0]
        proyectos = [p.strip() for p in str(fila["proyectos"]).split(",")]
        cecos = [c.strip() for c in str(fila["cecos"]).split(",")]
        return fila["usuario"], fila["rol"], proyectos, cecos
    return None, None, None, None

def filtro_pro(col):
    proyectos_local = proyectos.copy()
    proyectos_local["proyectos"] = proyectos_local["proyectos"].astype(str).str.strip()
    proyectos_local["nombre"] = proyectos_local["nombre"].astype(str).str.strip()
    allowed = [str(x).strip() for x in st.session_state.get("proyectos", [])]
    if allowed == ["ESGARI"]:
        df_visibles = proyectos_local.copy()
        opciones = ["ESGARI"] + df_visibles["nombre"].dropna().tolist()
        proyecto_nombre = col.selectbox("Selecciona un proyecto", opciones)

        if proyecto_nombre == "ESGARI":
            proyecto_codigo = df_visibles["proyectos"].tolist()  # todos
        else:
            proyecto_codigo = df_visibles.loc[df_visibles["nombre"] == proyecto_nombre, "proyectos"].tolist()

    else:
        df_visibles = proyectos_local[proyectos_local["proyectos"].isin(allowed)].copy()
        if df_visibles.empty:
            st.error("No hay proyectos visibles para este usuario. Revisa st.session_state['proyectos'] vs catálogo 'proyectos'.")
            st.stop()
        nombres_visibles = df_visibles["nombre"].dropna().unique().tolist()
        proyecto_nombre = col.selectbox("Selecciona un proyecto", nombres_visibles)
        proyecto_codigo = df_visibles.loc[df_visibles["nombre"] == proyecto_nombre, "proyectos"].astype(str).tolist()
    if not proyecto_codigo:
        st.error("No se encontró código para el proyecto seleccionado. Revisa duplicados o nombres en el catálogo.")
        st.stop()

    return proyecto_codigo, proyecto_nombre


def filtro_meses(col, df_ppt):
    meses_ordenados = ["ene.", "feb.", "mar.", "abr.", "may.", "jun.", "jul.", "ago.", "sep.", "oct.", "nov.", "dic."]
    meses_disponibles = [m for m in meses_ordenados if m in df_ppt["Mes_A"].unique()]

    if selected == "PPT MENSUAL":
        mes = col.selectbox("Selecciona un mes", meses_disponibles)
        return [mes]

    elif selected == "PPT YTD":
        mes_act = meses_disponibles[-1] if meses_disponibles else None
        index_default = meses_disponibles.index(mes_act) if mes_act in meses_disponibles else 0
        mes_sel = col.selectbox("Selecciona mes corte (YTD)", meses_disponibles, index=index_default)
        idx = meses_disponibles.index(mes_sel)
        return meses_disponibles[:idx + 1]

    else:
        return col.multiselect("Selecciona un mes", meses_disponibles, default=[meses_disponibles[0]] if meses_disponibles else [])

def porcentaje_ingresos(df, meses, pro, codigo_pro):
    if pro == "ESGARI":
        por_ingre = 1
    else:
        df_mes = df[df["Mes_A"].isin(meses)]
        df_ingresos = df_mes[df_mes["Categoria_A"] == "INGRESO"]

        ingreso_total = df_ingresos["Neto_A"].sum()

        df_pro = df_ingresos[df_ingresos["Proyecto_A"].isin(codigo_pro)]
        ingreso_proyecto = df_pro["Neto_A"].sum()

        por_ingre = ingreso_proyecto / ingreso_total if ingreso_total != 0 else 0

    return por_ingre

def ingreso (df, meses, codigo_pro, pro):
    if pro == "ESGARI":
        df_mes = df[df['Mes_A'].isin(meses)]
        df_ingresos = df_mes[df_mes['Categoria_A'] == 'INGRESO']
        ingreso_pro = df_ingresos['Neto_A'].sum()
    else:
        df_mes = df[df['Mes_A'].isin(meses)]
        df_pro = df_mes[df_mes['Proyecto_A'].isin(codigo_pro)]
        df_ingresos = df_pro[df_pro['Categoria_A'] == 'INGRESO']
        ingreso_pro = df_ingresos['Neto_A'].sum()
    return ingreso_pro

def coss(df, meses, codigo_pro, pro, lista_proyectos):
    pat_oh = ["8002", "8003", "8004"]
    if pro == "ESGARI":

        df = df[~df['Proyecto_A'].isin(pat_oh)]
        df_mes = df[df['Mes_A'].isin(meses)]
        df_coss = df_mes[df_mes['Clasificacion_A'] == 'COSS']
        coss_pro = df_coss['Neto_A'].sum()
        mal_clasificados = 0
    
    else:
        df_mes = df[df['Mes_A'].isin(meses)]
        df_pro = df_mes[df_mes['Proyecto_A'].isin(codigo_pro)]
        df_coss = df_pro[df_pro['Clasificacion_A'] == 'COSS']
        coss_pro = df_coss['Neto_A'].sum()
        for x in meses:
            por_ingresos = porcentaje_ingresos(df, [x], pro, codigo_pro)
            df_mes_x = df[df["Mes_A"] == x]
            mal_clasificados = df_mes_x[~df_mes_x["Proyecto_A"].isin(lista_proyectos)]
            mal_clasificados = mal_clasificados[mal_clasificados["Clasificacion_A"].isin(["COSS"])]["Neto_A"].sum() * por_ingresos
            coss_pro += mal_clasificados
    return coss_pro, mal_clasificados

def patio(df, meses, codigo_pro, proyecto_nombre):
    df['Proyecto_A'] = df['Proyecto_A'].astype(str)
    patio_t = 0
    for x in meses:
        proyectos_patio = ["3201", "3002", "1003", "2003"]

        df_mes = df[df['Mes_A'].isin([x])]

        if proyecto_nombre == "ESGARI":
            df_patio = df_mes[df_mes['Proyecto_A'] == "8003"]
            df_patio = df_patio[df_patio['Clasificacion_A'].isin(['COSS', 'G.ADMN'])]
            patio_t += df_patio['Neto_A'].sum()
        
        elif any(pro in proyectos_patio for pro in codigo_pro):
            df_patio = df_mes[df_mes['Proyecto_A'] == "8003"]
            df_patio = df_patio[df_patio['Clasificacion_A'].isin(['COSS', 'G.ADMN'])]
            patio = df_patio['Neto_A'].sum()

            ingre_pat = df_mes[df_mes['Proyecto_A'].isin(proyectos_patio)]
            ingre_pat = ingre_pat[ingre_pat['Clasificacion_A'] == 'INGRESO']
            ingre_pat = ingre_pat['Neto_A'].sum()

            ingreso_pro = ingreso(df, [x], codigo_pro, proyecto_nombre)
            por_patio = ingreso_pro / ingre_pat if ingre_pat != 0 else 0
            patio_t += por_patio * patio
        else:
            patio_t += 0
    return patio_t

def gadmn(df, meses, codigo_pro, pro, lista_proyectos, categorias_flex_com=None):
    """
    categorias_flex_com: lista de categorías para el ajuste de FLEX (si aplica)
    """
    categorias_flex_com = categorias_flex_com or []
    pat_oh = ["8002", "8003", "8004"]

    mal_clasificados_total = 0

    df_base = df[~df["Proyecto_A"].isin(pat_oh)].copy() if pro in ["ESGARI", "FLEX DEDICADO", "FLEX SPOT"] else df.copy()
    df_mes = df_base[df_base["Mes_A"].isin(meses)]

    if pro == "ESGARI":
        df_gadmn = df_mes[df_mes["Clasificacion_A"] == "G.ADMN"]
        return df_gadmn["Neto_A"].sum(), 0

    df_pro = df_mes[df_mes["Proyecto_A"].isin(codigo_pro)]
    df_gadmn = df_pro[df_pro["Clasificacion_A"] == "G.ADMN"]
    gadmn_pro = df_gadmn["Neto_A"].sum()

    if pro == "FLEX DEDICADO":
        gadmn_flexs = df_pro[df_pro["Categoria_A"].isin(categorias_flex_com)]["Neto_A"].sum() * 0.15
        gadmn_pro -= gadmn_flexs

    if pro == "FLEX SPOT":
        df_pro_flexd = df_mes[df_mes["Proyecto_A"].isin(["2001"])]
        gadmn_flexd = df_pro_flexd[df_pro_flexd["Categoria_A"].isin(categorias_flex_com)]["Neto_A"].sum() * 0.15
        gadmn_pro += gadmn_flexd

    for x in meses:
        por_ing = porcentaje_ingresos(df_base, [x], pro, codigo_pro)
        df_mes_x = df_base[df_base["Mes_A"] == x]
        mal = df_mes_x[~df_mes_x["Proyecto_A"].isin(lista_proyectos)]
        mal = mal[mal["Clasificacion_A"].isin(["G.ADMN"])]["Neto_A"].sum() * por_ing
        gadmn_pro += mal
        mal_clasificados_total += mal

    return gadmn_pro, mal_clasificados_total

def oh(df, meses, codigo_pro, nombre_proyecto):
    oh_pro = 0
    for x in meses:
        oh = ["8002", "8004"]
        df_mes = df[df['Mes_A'].isin([x])]
        por_ingre = porcentaje_ingresos(df, [x], nombre_proyecto, codigo_pro)
        df_oh = df_mes[df_mes['Proyecto_A'].isin(oh)]
        df_oh = df_oh[df_oh['Clasificacion_A'].isin(['COSS', 'G.ADMN'])]
        oh_coss = df_oh['Neto_A'].sum()
        oh_pro += oh_coss * por_ingre
    return oh_pro

def gasto_fin (df, meses, codigo_pro, pro, lista_proyectos):
    if pro == "ESGARI":
        df_mes = df[df['Mes_A'].isin(meses)]
        df_gasto_fin = df_mes[df_mes['Clasificacion_A'] == 'GASTOS FINANCIEROS']
        gasto_fin = df_gasto_fin['Neto_A'].sum()
        mal_clasificados = 0
        oh_gasto_fin = 0
    else:
        df_mes = df[df['Mes_A'].isin(meses)]
        df_pro = df_mes[df_mes['Proyecto_A'].isin(codigo_pro)]
        df_gasto_fin = df_pro[df_pro['Clasificacion_A'] == 'GASTOS FINANCIEROS']
        gasto_fin = df_gasto_fin['Neto_A'].sum()
        for x in meses:
            por_ingresos = porcentaje_ingresos(df, [x], pro, codigo_pro)
            df_mes_x = df[df["Mes_A"] == x]
            mal_clasificados = df_mes_x[~df_mes_x["Proyecto_A"].isin(lista_proyectos)]
            mal_clasificados = mal_clasificados[mal_clasificados["Clasificacion_A"].isin(["GASTOS FINANCIEROS"])]["Neto_A"].sum() * por_ingresos
            gasto_fin += mal_clasificados
            oh_gasto_fin = df_mes_x[df_mes_x['Proyecto_A'].isin(["8002", "8003","8004"])]
            oh_gasto_fin = oh_gasto_fin[oh_gasto_fin['Clasificacion_A'].isin(["GASTOS FINANCIEROS"])]
            oh_gasto_fin = oh_gasto_fin['Neto_A'].sum() * por_ingresos
            gasto_fin += oh_gasto_fin

    return gasto_fin, mal_clasificados, oh_gasto_fin

def ingreso_fin (df, meses, codigo_pro, pro, lista_proyectos):
    ing_fin_cat = ["INGRESO POR REVALUACION CAMBIARIA", "INGRESO POR FACTORAJE", "INGRESOS POR INTERESES"]
    if pro == "ESGARI":
        df_mes = df[df['Mes_A'].isin(meses)]
        df_ingreso_fin = df_mes[df_mes['Categoria_A'].isin(ing_fin_cat)]
        ingreso_fin = df_ingreso_fin['Neto_A'].sum()
        mal_clasificados = 0
        oh_ingreso_fin = 0
    else:
        df_mes = df[df['Mes_A'].isin(meses)]
        df_pro = df_mes[df_mes['Proyecto_A'].isin(codigo_pro)]
        df_ingreso_fin = df_pro[df_pro['Categoria_A'].isin(ing_fin_cat)]
        ingreso_fin = df_ingreso_fin['Neto_A'].sum()
        for x in meses:
            por_ingresos = porcentaje_ingresos(df, [x], pro, codigo_pro)
            df_mes_x = df[df["Mes_A"] == x]
            mal_clasificados = df_mes_x[~df_mes_x["Proyecto_A"].isin(lista_proyectos)]
            mal_clasificados = mal_clasificados[mal_clasificados["Categoria_A"].isin(ing_fin_cat)]["Neto_A"].sum() * por_ingresos
            ingreso_fin += mal_clasificados
            oh_ingreso_fin = df_mes_x[df_mes_x['Proyecto_A'].isin(["8002", "8003", "8004"])]
            oh_ingreso_fin = oh_ingreso_fin[oh_ingreso_fin['Categoria_A'].isin(ing_fin_cat)]
            oh_ingreso_fin = oh_ingreso_fin['Neto_A'].sum() * por_ingresos
            ingreso_fin += oh_ingreso_fin


    return ingreso_fin, mal_clasificados, oh_ingreso_fin

def estado_resultado(df_ppt, meses_seleccionado, proyecto_nombre, proyecto_codigo, lista_proyectos):
    estado_resultado = {}

    por_ingre = porcentaje_ingresos(df_ppt, meses_seleccionado, proyecto_nombre, proyecto_codigo)
    ingreso_proyecto = ingreso(df_ppt, meses_seleccionado, proyecto_codigo, proyecto_nombre)
    coss_pro, mal_coss = coss(df_ppt, meses_seleccionado, proyecto_codigo, proyecto_nombre, lista_proyectos)
    patio_pro = patio(df_ppt, meses_seleccionado, proyecto_codigo, proyecto_nombre)
    por_patio = patio_pro / ingreso_proyecto if ingreso_proyecto != 0 else 0
    coss_total = coss_pro + patio_pro
    por_coss = coss_total / ingreso_proyecto if ingreso_proyecto != 0 else 0
    utilidad_bruta = ingreso_proyecto - coss_total
    por_ub = utilidad_bruta / ingreso_proyecto if ingreso_proyecto != 0 else 0
    gadmn_pro, mal_gadmn = gadmn(df_ppt, meses_seleccionado, proyecto_codigo, proyecto_nombre, lista_proyectos)
    por_gadmn = gadmn_pro / ingreso_proyecto if ingreso_proyecto != 0 else 0
    utilidad_operativa = utilidad_bruta - gadmn_pro
    por_utilidad_operativa = utilidad_operativa / ingreso_proyecto if ingreso_proyecto != 0 else 0
    oh_pro = oh(df_ppt, meses_seleccionado, proyecto_codigo, proyecto_nombre)
    por_oh = oh_pro / ingreso_proyecto if ingreso_proyecto != 0 else 0
    ebit = utilidad_operativa - oh_pro
    por_ebit = ebit / ingreso_proyecto if ingreso_proyecto != 0 else 0
    gasto_fin_pro, mal_gfin, oh_pro_gfin = gasto_fin(df_ppt, meses_seleccionado, proyecto_codigo, proyecto_nombre, lista_proyectos)
    por_gasto_fin = gasto_fin_pro / ingreso_proyecto if ingreso_proyecto != 0 else 0
    ingreso_fin_pro, mal_ifin, oh_pro_ifin = ingreso_fin(df_ppt, meses_seleccionado, proyecto_codigo, proyecto_nombre, lista_proyectos)
    por_ingreso_fin = ingreso_fin_pro / ingreso_proyecto if ingreso_proyecto != 0 else 0
    resultado_fin = gasto_fin_pro - ingreso_fin_pro
    por_resultado_fin = resultado_fin / ingreso_proyecto if ingreso_proyecto != 0 else 0
    ebt = ebit - resultado_fin
    por_ebt = ebt / ingreso_proyecto if ingreso_proyecto != 0 else 0

    estado_resultado.update({
        'porcentaje_ingresos': por_ingre,
        'ingreso_proyecto': ingreso_proyecto,
        'coss_pro': coss_pro,
        'mal_coss': mal_coss,
        'patio_pro': patio_pro,
        'por_patio': por_patio,
        'coss_total': coss_total,
        'por_coss': por_coss,
        'utilidad_bruta': utilidad_bruta,
        'por_utilidad_bruta': por_ub,
        'gadmn_pro': gadmn_pro,
        'mal_gadmn': mal_gadmn,
        'por_gadmn': por_gadmn,
        'utilidad_operativa': utilidad_operativa,
        'por_utilidad_operativa': por_utilidad_operativa,
        'oh_pro': oh_pro,
        'por_oh': por_oh,
        'ebit': ebit,
        'por_ebit': por_ebit,
        'gasto_fin_pro': gasto_fin_pro,
        'mal_gfin': mal_gfin,
        'oh_pro_gfin': oh_pro_gfin,
        'por_gasto_fin': por_gasto_fin,
        'ingreso_fin_pro': ingreso_fin_pro,
        'por_ingreso_fin': por_ingreso_fin,
        'mal_ifin': mal_ifin,
        'oh_pro_ifin': oh_pro_ifin,
        'resultado_fin': resultado_fin,
        'por_resultado_fin': por_resultado_fin,
        'ebt': ebt,
        'por_ebt': por_ebt
    })

    return estado_resultado


def filtro_ceco(col):
    df_cecos = cargar_datos(cecos_url)
    df_cecos["ceco"] = df_cecos["ceco"].astype(str).str.strip()
    df_cecos["nombre"] = df_cecos["nombre"].astype(str).str.strip()

    allowed = [str(x).strip() for x in st.session_state.get("cecos", [])]
    if allowed == ["ESGARI"]:
        opciones = ["ESGARI"] + df_cecos["nombre"].dropna().unique().tolist()
        ceco_nombre = col.selectbox("Selecciona un ceco", opciones)

        if ceco_nombre == "ESGARI":
            ceco_codigo = df_cecos["ceco"].dropna().unique().tolist()
        else:
            ceco_codigo = df_cecos.loc[df_cecos["nombre"] == ceco_nombre, "ceco"].dropna().unique().tolist()

        return ceco_codigo, ceco_nombre
    df_visibles = df_cecos[df_cecos["ceco"].isin(allowed)].copy()
    if df_visibles.empty:
        col.error("No tienes CeCos asignados o no coinciden con el catálogo.")
        return [], None
    nombre_a_codigo = dict(zip(df_visibles["nombre"], df_visibles["ceco"]))
    opciones = list(nombre_a_codigo.keys())
    ceco_nombre = col.selectbox("Selecciona un ceco", opciones)
    ceco_codigo = [nombre_a_codigo.get(ceco_nombre)] if ceco_nombre in nombre_a_codigo else []
    return ceco_codigo, ceco_nombre


def tabla_comparativa(tipo_com, df_agrid, df_ppt, proyecto_codigo, meses_seleccionado, clasificacion, categoria, titulo):
    st.write(titulo)
    df_agrid = df_agrid.copy()
    df_ppt = df_ppt.copy()
    df_agrid["Proyecto_A"] = df_agrid["Proyecto_A"].astype(str).str.strip()
    df_ppt["Proyecto_A"] = df_ppt["Proyecto_A"].astype(str).str.strip()
    proyecto_codigo = [str(x) for x in proyecto_codigo]

    columnas = ['Cuenta_Nombre_A', 'Categoria_A']
    df_agrid = df_agrid[df_agrid[clasificacion] == categoria]
    df_agrid = df_agrid.groupby(columnas, as_index=False).agg({"Neto_A": "sum"})
    df_agrid.rename(columns={"Neto_A": f"{tipo_com}"}, inplace=True)
    df_actual = df_ppt[df_ppt['Mes_A'].isin(meses_seleccionado)]
    df_actual = df_actual[df_actual['Proyecto_A'].isin(proyecto_codigo)]
    df_actual = df_actual[df_actual[clasificacion] == categoria]
    df_actual = df_actual.groupby(columnas, as_index=False).agg({"Neto_A": "sum"})
    df_actual.rename(columns={"Neto_A": "YTD"}, inplace=True)
    df_compara = pd.merge(df_agrid, df_actual, on=columnas, how="outer").fillna(0)
    df_compara["Variación % "] = np.where(
        df_compara[f"{tipo_com}"] != 0,
        ((df_compara["YTD"] / df_compara[f"{tipo_com}"]) - 1) * 100,
        0
    )

    cols_out = ['Cuenta_Nombre_A', 'Categoria_A', 'YTD', f"{tipo_com}", "Variación % "]
    df_tabla = df_compara[cols_out].copy()
    df_last = df_tabla.groupby("Categoria_A", as_index=False)[["YTD", f"{tipo_com}"]].sum()
    df_last["Variación % "] = np.where(
        df_last[f"{tipo_com}"] != 0,
        ((df_last["YTD"] / df_last[f"{tipo_com}"]) - 1) * 100,
        0
    )
    df_tabla = pd.concat([df_tabla, df_last], ignore_index=True)
    df_tabla["YTD"] = pd.to_numeric(df_tabla["YTD"], errors="coerce").fillna(0)
    df_tabla[tipo_com] = pd.to_numeric(df_tabla[tipo_com], errors="coerce").fillna(0)
    df_tabla["Variación % "] = pd.to_numeric(df_tabla["Variación % "], errors="coerce").fillna(0)

    # AgGrid (agrupado)
    gb = GridOptionsBuilder.from_dataframe(df_tabla)
    gb.configure_default_column(groupable=True)

    gb.configure_column("Categoria_A", rowGroup=True, hide=True)

    gb.configure_column("YTD", type=["numericColumn"], aggFunc="sum", valueFormatter="`$${value.toLocaleString()}`")
    gb.configure_column(f"{tipo_com}", type=["numericColumn"], aggFunc="sum", valueFormatter="`$${value.toLocaleString()}`")
    gb.configure_column("Variación % ", header_name="Variación % ", type=["numericColumn"], aggFunc="avg", valueFormatter="(value != null) ? value.toFixed(2) + ' %' : ''")

    grid_options = gb.build()
    grid_options.update({
        "groupDisplayType": "groupRows",
        "groupDefaultExpanded": 0
    })

    AgGrid(
        df_tabla,
        gridOptions=grid_options,
        enable_enterprise_modules=True,
        height=500,
        use_checkbox=False,
        fit_columns_on_grid_load=True,
        theme="streamlit",
        key=f"agrid_{tipo_com}_{'-'.join(proyecto_codigo)}_{'-'.join(meses_seleccionado)}_{categoria}"
    )
def seccion_analisis_especial_porcentual(
    df_ppt, df_real, ingreso,
    meses_seleccionado, proyecto_codigo, proyecto_nombre,
    ceco_codigo, ceco_nombre,
    funcion, nombre_funcion
):
    with st.expander(f"{nombre_funcion.upper()}"):

        meses_completos = ["ene.", "feb.", "mar.", "abr.", "may.", "jun.", "jul.", "ago.", "sep.", "oct.", "nov.", "dic."]
        orden = {m:i for i, m in enumerate(meses_completos)}
        meses_sel = sorted(list(set(meses_seleccionado)), key=lambda x: orden.get(x, 999))

        if not meses_sel:
            st.error("Selecciona por lo menos un mes.")
            return

        proy = [str(x).strip() for x in proyecto_codigo]
        cecos = [str(x).strip() for x in ceco_codigo]
        df_ppt_sel = df_ppt[
            (df_ppt["Mes_A"].isin(meses_sel)) &
            (df_ppt["Proyecto_A"].astype(str).isin(proy)) &
            (df_ppt["CeCo_A"].astype(str).isin(cecos))
        ].copy()

        ingreso_ppt = ingreso(df_ppt_sel, meses_sel, proy, proyecto_nombre)
        valor_ppt = funcion(df_ppt_sel, meses_sel, proy, proyecto_nombre)
        ppt_pct = (valor_ppt / ingreso_ppt * 100) if ingreso_ppt != 0 else 0.0
        df_real_sel = df_real[
            (df_real["Mes_A"].isin(meses_sel)) &
            (df_real["Proyecto_A"].astype(str).isin(proy)) &
            (df_real["CeCo_A"].astype(str).isin(cecos))
        ].copy()

        ingreso_real = ingreso(df_real_sel, meses_sel, proy, proyecto_nombre)
        valor_real = funcion(df_real_sel, meses_sel, proy, proyecto_nombre)
        real_pct = (valor_real / ingreso_real * 100) if ingreso_real != 0 else 0.0

        dif_pp = real_pct - ppt_pct
        pct_vs_ppt = ((real_pct / ppt_pct) - 1) * 100 if ppt_pct != 0 else 0.0

        df_out = pd.DataFrame([{
            "PPT %": round(ppt_pct, 2),
            "REAL %": round(real_pct, 2),
            "DIF (pp)": round(dif_pp, 2),
            "% vs PPT": round(pct_vs_ppt, 2)
        }])

        def resaltar(row):
            if row["REAL %"] > row["PPT %"]:
                return ['background-color: red; color: white'] * len(row)
            elif row["REAL %"] < row["PPT %"]:
                return ['background-color: green; color: black'] * len(row)
            return [''] * len(row)

        st.dataframe(
            df_out.style.apply(resaltar, axis=1).format({
                "PPT %": "{:.2f}%",
                "REAL %": "{:.2f}%",
                "DIF (pp)": "{:.2f}",
                "% vs PPT": "{:.2f}%"
            }),
            use_container_width=True
        )
def seccion_analisis_por_clasificacion(
    df_ppt, df_real, ingreso,
    meses_seleccionado, proyecto_codigo, proyecto_nombre,
    clasificacion_nombre, ceco_codigo, ceco_nombre
):
    with st.expander(clasificacion_nombre):

        meses_completos = ["ene.", "feb.", "mar.", "abr.", "may.", "jun.", "jul.", "ago.", "sep.", "oct.", "nov.", "dic."]
        orden = {m:i for i, m in enumerate(meses_completos)}
        meses_sel = sorted(list(set(meses_seleccionado)), key=lambda x: orden.get(x, 999))

        if not meses_sel:
            st.error("Selecciona por lo menos un mes.")
            return

        proy = [str(x).strip() for x in proyecto_codigo]
        cecos = [str(x).strip() for x in ceco_codigo]
        df_ppt_sel = df_ppt[
            (df_ppt["Mes_A"].isin(meses_sel)) &
            (df_ppt["Proyecto_A"].astype(str).isin(proy)) &
            (df_ppt["CeCo_A"].astype(str).isin(cecos))
        ].copy()

        ingreso_ppt_sel = ingreso(df_ppt_sel, meses_sel, proy, proyecto_nombre)

        df_ppt_sel = df_ppt_sel[df_ppt_sel["Categoria_A"] != "INGRESO"]
        df_ppt_sel = df_ppt_sel[df_ppt_sel["Clasificacion_A"] == clasificacion_nombre]

        ppt_cla_nom = df_ppt_sel.groupby(["Clasificacion_A"], as_index=False)["Neto_A"].sum()
        ppt_cat_nom = df_ppt_sel.groupby(["Clasificacion_A", "Categoria_A"], as_index=False)["Neto_A"].sum()
        ppt_cta_nom = df_ppt_sel.groupby(["Clasificacion_A", "Categoria_A", "Cuenta_Nombre_A"], as_index=False)["Neto_A"].sum()
        ppt_cla_nom["PPT %"] = np.where(ingreso_ppt_sel != 0, (ppt_cla_nom["Neto_A"] / ingreso_ppt_sel) * 100, 0.0)
        ppt_cat_nom["PPT %"] = np.where(ingreso_ppt_sel != 0, (ppt_cat_nom["Neto_A"] / ingreso_ppt_sel) * 100, 0.0)
        cat_map_ppt = dict(zip(ppt_cat_nom["Categoria_A"], ppt_cat_nom["Neto_A"]))
        ppt_cta_nom["Cat_Total"] = ppt_cta_nom["Categoria_A"].map(cat_map_ppt).fillna(0)
        ppt_cta_nom["PPT % CTA"] = np.where(ppt_cta_nom["Cat_Total"] != 0, (ppt_cta_nom["Neto_A"] / ppt_cta_nom["Cat_Total"]) * 100, 0.0)

        df_real_sel = df_real[
            (df_real["Mes_A"].isin(meses_sel)) &
            (df_real["Proyecto_A"].astype(str).isin(proy)) &
            (df_real["CeCo_A"].astype(str).isin(cecos))
        ].copy()

        ingreso_real_sel = ingreso(df_real_sel, meses_sel, proy, proyecto_nombre)

        df_real_sel = df_real_sel[df_real_sel["Categoria_A"] != "INGRESO"]
        df_real_sel = df_real_sel[df_real_sel["Clasificacion_A"] == clasificacion_nombre]
        real_cla_nom = df_real_sel.groupby(["Clasificacion_A"], as_index=False)["Neto_A"].sum()
        real_cat_nom = df_real_sel.groupby(["Clasificacion_A", "Categoria_A"], as_index=False)["Neto_A"].sum()
        real_cta_nom = df_real_sel.groupby(["Clasificacion_A", "Categoria_A", "Cuenta_Nombre_A"], as_index=False)["Neto_A"].sum()
        real_cla_nom["REAL %"] = np.where(ingreso_real_sel != 0, (real_cla_nom["Neto_A"] / ingreso_real_sel) * 100, 0.0)
        real_cat_nom["REAL %"] = np.where(ingreso_real_sel != 0, (real_cat_nom["Neto_A"] / ingreso_real_sel) * 100, 0.0)
        cat_map_real = dict(zip(real_cat_nom["Categoria_A"], real_cat_nom["Neto_A"]))
        real_cta_nom["Cat_Total"] = real_cta_nom["Categoria_A"].map(cat_map_real).fillna(0)
        real_cta_nom["REAL % CTA"] = np.where(real_cta_nom["Cat_Total"] != 0, (real_cta_nom["Neto_A"] / real_cta_nom["Cat_Total"]) * 100, 0.0)
        df_cla = ppt_cla_nom.merge(real_cla_nom[["Clasificacion_A", "REAL %"]], on="Clasificacion_A", how="outer").fillna(0)
        df_cla["DIF (pp)"] = df_cla["REAL %"] - df_cla["PPT %"]
        df_cla["% vs PPT"] = np.where(df_cla["PPT %"] != 0, (df_cla["REAL %"] / df_cla["PPT %"] - 1) * 100, 0.0)

        def resaltar(row):
            if row["REAL %"] > row["PPT %"]:
                return ['background-color: red; color: white'] * len(row)
            elif row["REAL %"] < row["PPT %"]:
                return ['background-color: green; color: black'] * len(row)
            return [''] * len(row)

        st.markdown("### Resumen Clasificación (sobre Ingresos)")
        st.dataframe(
            df_cla.set_index("Clasificacion_A").style
                .apply(resaltar, axis=1)
                .format({
                    "PPT %": "{:.2f}%",
                    "REAL %": "{:.2f}%",
                    "DIF (pp)": "{:.2f}",
                    "% vs PPT": "{:.2f}%"
                }),
            use_container_width=True
        )
        df_cat = ppt_cat_nom.merge(real_cat_nom[["Clasificacion_A", "Categoria_A", "REAL %"]], on=["Clasificacion_A", "Categoria_A"], how="outer").fillna(0)
        df_cat["DIF (pp)"] = df_cat["REAL %"] - df_cat["PPT %"]
        df_cat["% vs PPT"] = np.where(df_cat["PPT %"] != 0, (df_cat["REAL %"] / df_cat["PPT %"] - 1) * 100, 0.0)

        df_cta = ppt_cta_nom.merge(
            real_cta_nom[["Clasificacion_A", "Categoria_A", "Cuenta_Nombre_A", "REAL % CTA"]],
            on=["Clasificacion_A", "Categoria_A", "Cuenta_Nombre_A"],
            how="outer"
        ).fillna(0)

        df_cta["DIF (pp)"] = df_cta["REAL % CTA"] - df_cta["PPT % CTA"]
        df_cta["% vs PPT"] = np.where(df_cta["PPT % CTA"] != 0, (df_cta["REAL % CTA"] / df_cta["PPT % CTA"] - 1) * 100, 0.0)

        df_cat_out = df_cat[["Categoria_A", "PPT %", "REAL %", "DIF (pp)", "% vs PPT"]].copy()
        df_cat_out["Cuenta_Nombre_A"] = ""

        df_cta_out = df_cta[["Categoria_A", "Cuenta_Nombre_A", "PPT % CTA", "REAL % CTA", "DIF (pp)", "% vs PPT"]].copy()
        df_cta_out = df_cta_out.rename(columns={"PPT % CTA": "PPT %", "REAL % CTA": "REAL %"})

        df_out = pd.concat([df_cat_out, df_cta_out], ignore_index=True)

        gb = GridOptionsBuilder.from_dataframe(df_out)
        gb.configure_default_column(groupable=True)
        gb.configure_column("Categoria_A", rowGroup=True, hide=True)
        gb.configure_column("Cuenta_Nombre_A", header_name="Cuenta", pinned="left")

        pct_formatter = JsCode("""
            function(params) {
                if (params.value === null || params.value === undefined) return '';
                return params.value.toFixed(2) + ' %';
            }
        """)
        for col in ["PPT %", "REAL %", "DIF (pp)", "% vs PPT"]:
            gb.configure_column(col, type=["numericColumn"], aggFunc="last", valueFormatter=pct_formatter)

        gridOptions = gb.build()
        meses_key = "-".join(meses_sel)
        grid_key = f"agrid_cla_{clasificacion_nombre}_{'-'.join(proy)}_{'-'.join(cecos)}_{meses_key}"

        st.markdown("### Categoría (sobre ingresos) + Cuenta (% de su Categoría)")
        AgGrid(
            df_out,
            gridOptions=gridOptions,
            allow_unsafe_jscode=True,
            enable_enterprise_modules=True,
            height=520,
            use_checkbox=False,
            fit_columns_on_grid_load=True,
            theme="streamlit",
            key=grid_key
        )
def agrid_ingreso_con_totales(df):
    df = df.copy()

    # Nos quedamos solo con INGRESO (si quieres otras categorías, quita este filtro)
    df_g = (
        df[df["Categoria_A"] == "INGRESO"]
        .groupby(["Categoria_A", "Cuenta_A", "Cuenta_Nombre_A"], as_index=False)
        .agg({"Neto_A": "sum"})
    )

    currency_formatter = JsCode("""
    function(params) {
        if (params.value === null || params.value === undefined) return "";
        return new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN' }).format(params.value);
    }
    """)

    gb = GridOptionsBuilder.from_dataframe(df_g)
    gb.configure_default_column(resizable=True, sortable=True, filter=True)
    gb.configure_column("Categoria_A", rowGroup=True, hide=True)
    gb.configure_column("Cuenta_A", header_name="Cuenta", pinned="left")
    gb.configure_column("Cuenta_Nombre_A", header_name="Cuenta_Nombre_A", pinned="left")

    gb.configure_column(
        "Neto_A",
        header_name="Total (MXN)",
        type=["numericColumn"],
        aggFunc="sum",
        valueFormatter=currency_formatter
    )

    grid_options = gb.build()
    grid_options.update({
        "groupDisplayType": "groupRows",
        "groupDefaultExpanded": 1,
        "suppressAggFuncInHeader": True
    })

    AgGrid(
        df_g,
        gridOptions=grid_options,
        enable_enterprise_modules=True,
        allow_unsafe_jscode=True,
        fit_columns_on_grid_load=True,
        height=420,
        theme="streamlit",
        key="agrid_ingreso_totales_nominal"
    )
init_session_state()
# App principal
df_usuarios = cargar_datos(Usuarios_url)

if not st.session_state["logged_in"]:

    st.title("🔐 Inicio de Sesión presupuesto")

    with st.form("login_form"):
        username = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        submitted = st.form_submit_button("Iniciar sesión")

        if submitted:
            user, rol, proyectos, cecos = validar_credenciales(df_usuarios, username, password)
            if user:
                st.session_state["logged_in"] = True
                st.session_state["username"] = user
                st.session_state["rol"] = rol
                st.session_state["proyectos"] = proyectos
                st.session_state["cecos"] = cecos
                st.success("¡Inicio de sesión exitoso!")
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos")
else:
    df_ppt = cargar_datos(base_ppt)
    df_ppt = (
    df_ppt
    .groupby([
        "Mes_A", "Empresa_A", "CeCo_A", "Proyecto_A", "Cuenta_A",
        "Clasificacion_A", "Cuenta_Nombre_A", "Categoria_A"
    ], as_index=False)["Neto_A"]
    .sum()
)

    df_real = cargar_datos(basereal)
    df_real = (
    df_real
    .groupby([
        "Mes_A", "Empresa_A", "CeCo_A", "Proyecto_A", "Cuenta_A",
        "Clasificacion_A", "Cuenta_Nombre_A", "Categoria_A"
    ], as_index=False)["Neto_A"]
    .sum()
)
    
    proyectos = cargar_datos(proyectos_url)

    df_ppt["Proyecto_A"] = df_ppt["Proyecto_A"].astype(str).str.strip()
    df_real["Proyecto_A"] = df_real["Proyecto_A"].astype(str).str.strip()
    proyectos["proyectos"] = proyectos["proyectos"].astype(str).str.strip()
    list_pro = proyectos["proyectos"].tolist()
    st.sidebar.success(f"👤 Usuario: {st.session_state['username']}")

    if st.sidebar.button("Cerrar sesión"):
        for key in ["logged_in", "username", "rol"]:
            st.session_state[key] = "" if key != "logged_in" else False
        st.rerun()
    if st.session_state['rol'] == "admin":
        if st.sidebar.button("🔄 Recargar datos"):
            st.cache_data.clear()
            st.rerun()
    if st.session_state["rol"] in ["admin"] and "ESGARI" in st.session_state["proyectos"]:
        selected = option_menu(
            menu_title=None,
            options=["PPT YTD", "PPT VS ACTUAL", "Ingresos", "OH", "Departamentos", "Consulta", "Meses PPT", "Variaciones", "Comparativa", "Objetivos"],
            icons=[
            "calendar-range",     # PPT YTD
            "bar-chart-steps",    # PPT VS ACTUAL
            "cash-coin",          # Ingresos
            "building",           # OH (Overhead / oficinas)
            "diagram-3",          # Departamentos
            "search",             # Consulta
            "calendar-month",     # Meses PPT
            "arrow-left-right",   # Variaciones
            "bar-chart",          # Comparativa
            "bullseye",           # Objetivos
        ],
            default_index=0,
            orientation="horizontal",
        )
    elif st.session_state["rol"] == "director" or st.session_state["rol"] == "admin":
        selected = option_menu(
        menu_title=None,
        options=["PPT YTD", "PPT VS ACTUAL", "Ingresos", "OH", "Departamentos", "Consulta", "Meses PPT", "Variaciones", "Comparativa", "Objetivos"],
        icons=["Calendar-range", "bar-chart-steps", "cash-coin", "building", "diagram-3", "search", "calendar-month", "arrow-left-right", "bar-chart", "bullseye"],
        default_index=0,
        orientation="horizontal",)

    elif st.session_state["rol"] == "gerente":
        selected = option_menu(
        menu_title=None,
        options=["PPT VS ACTUAL", "Ingresos", "OH", "Departamentos", "Consulta", "Meses PPT"],
        icons=["Calendar-range", "bar-chart-steps", "building", "diagram-3", "search", "calendar-month"],
        default_index=0,
        orientation="horizontal",)

    elif st.session_state["rol"] == "ceco":
        selected = option_menu(
        menu_title=None,
        options=[ "Departamentos", "Consulta"],
        icons=[ "diagram-3", "search"],
        default_index=0,
        orientation="horizontal",)


    if selected == "PPT YTD":

        def tabla_ppt_ytd(df_ppt):
            """
            PPT YTD = acumulado desde ene. hasta el mes seleccionado.
            """
            meses_ordenados = ["ene.", "feb.", "mar.", "abr.", "may.", "jun.", "jul.", "ago.", "sep.", "oct.", "nov.", "dic."]
            meses_disponibles = [m for m in meses_ordenados if m in df_ppt["Mes_A"].unique().tolist()]

            if not meses_disponibles:
                st.error("No hay meses disponibles en df_ppt (Mes_A).")
                return None
            col_filtro, _ = st.columns([1, 5])
            mes_corte = col_filtro.selectbox(
                "Mes corte YTD",
                meses_disponibles,
                index=len(meses_disponibles) - 1
            )

            idx = meses_disponibles.index(mes_corte)
            meses_ytd = meses_disponibles[: idx + 1]

            # ----------- LOGICA ORIGINAL (SIN CAMBIOS) ----------
            resumen_proyectos = {
                nombre: estado_resultado(
                    df_ppt,
                    meses_ytd,
                    nombre,
                    [str(codigo)],
                    list_pro
                )
                for nombre, codigo in zip(proyectos["nombre"], proyectos["proyectos"].astype(str))
                if nombre not in {"OFICINAS LUNA", "PATIO", "OFICINAS ANDARES"}
            }

            codigos = proyectos["proyectos"].astype(str).tolist()
            resumen_proyectos["ESGARI"] = estado_resultado(df_ppt, meses_ytd, "ESGARI", codigos, list_pro)

            metricas_seleccionadas = [
                ("Ingreso", "ingreso_proyecto"),
                ("COSS Total", "coss_total"),
                ("Utilidad Bruta", "utilidad_bruta"),
                ("Margen U.B. %", "por_utilidad_bruta"),
                ("G.ADMN", "gadmn_pro"),
                ("Utilidad Operativa", "utilidad_operativa"),
                ("Margen U.O. %", "por_utilidad_operativa"),
                ("OH", "oh_pro"),
                ("EBIT", "ebit"),
                ("Margen EBIT %", "por_ebit"),
                ("Gasto Fin", "gasto_fin_pro"),
                ("Ingreso Fin", "ingreso_fin_pro"),
                ("EBT", "ebt"),
                ("Margen EBT %", "por_ebt"),
            ]

            # ----------- CONSTRUIR TABLA ----------
            df_data = []
            for nombre_metrica, clave in metricas_seleccionadas:
                fila = {"Métrica": nombre_metrica}
                for proyecto, datos in resumen_proyectos.items():
                    fila[proyecto] = datos.get(clave, None)
                df_data.append(fila)

            df_tabla = pd.DataFrame(df_data)
            ratios = {
                "Margen U.B. %", "Margen U.O. %", "Margen EBIT %", "Margen EBT %"
            }

            def fmt_money(x):
                if pd.isna(x): return ""
                return f"${float(x):,.0f}"

            def fmt_pct(x):
                if pd.isna(x): return ""
                return f"{float(x)*100:,.2f}%"

            df_fmt = df_tabla.copy()
            for i in range(len(df_fmt)):
                met = df_fmt.loc[i, "Métrica"]
                for col in df_fmt.columns:
                    if col == "Métrica":
                        continue
                    df_fmt.loc[i, col] = fmt_pct(df_tabla.loc[i, col]) if met in ratios else fmt_money(df_tabla.loc[i, col])

            def style_row(row):
                if row["Métrica"] in ratios:
                    return ["background-color: #001F5B; color: white; font-weight: 700;"] * len(row)
                return [""] * len(row)

            st.subheader(f"PPT YTD al mes de {mes_corte}")

            # Header azul
            st.markdown("""
                <style>
                div[data-testid="stDataFrame"] thead tr th {
                    background-color: #001F5B !important;
                    color: white !important;
                    font-weight: 800 !important;
                }
                </style>
            """, unsafe_allow_html=True)

            st.dataframe(
                df_fmt.style.apply(style_row, axis=1),
                use_container_width=True,
                height=520
            )
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                df_tabla.to_excel(writer, index=False, sheet_name="Resumen")
            output.seek(0)

            st.download_button(
                label="📥 Descargar Excel",
                data=output,
                file_name=f"resumen_estado_resultado_PPT_YTD_{mes_corte}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            return df_tabla
        tabla_ppt_ytd(df_ppt)

    elif selected == "PPT VS ACTUAL":
        def _tabla_resumen_style(df_resumen):
            BLUE = "#00112B"

            def color_margenes(row):
                if "MARGEN" in str(row["CONCEPTO"]).upper():
                    return [f"background-color: {BLUE}; color: white; font-weight: 700;"] * len(row)
                return [""] * len(row)

            return (
                df_resumen.style
                .set_table_styles([
                    {"selector": "thead th",
                    "props": f"background-color: {BLUE}; color: white; font-weight: 700; font-size: 14px;"},
                    {"selector": "tbody td",
                    "props": "font-size: 13px;"},
                ])
                .apply(color_margenes, axis=1)
                .format({
                    "PPT": "${:,.2f}",
                    "REAL": "${:,.2f}",
                    "DIF": "${:,.2f}",
                    "VARIACIÓN %": "{:.2f}%"
                })
            )
        def tabla_variacion_pct(df_ppt, df_real, meses_seleccionado, proyecto_nombre, proyecto_codigo):
            if not meses_seleccionado:
                st.error("Favor de seleccionar por lo menos un mes")
                return None

            ppt = estado_resultado(df_ppt, meses_seleccionado, proyecto_nombre, proyecto_codigo, list_pro)
            real = estado_resultado(df_real, meses_seleccionado, proyecto_nombre, proyecto_codigo, list_pro)
            metricas_base = [
                ("Ingreso", "ingreso_proyecto", False),
                ("COSS", "coss_pro", False),
                ("COSS Patio", "patio_pro", False),
                ("COSS Total", "coss_total", False),
                ("Utilidad Bruta", "utilidad_bruta", False),
                ("Margen U.B.", "por_utilidad_bruta", True),
                ("G.ADMN", "gadmn_pro", False),
                ("Utilidad Operativa", "utilidad_operativa", False),
                ("Margen U.O.", "por_utilidad_operativa", True),
            ]

            metricas_extra = [
                ("OH", "oh_pro", False),
                ("Margen OH", "por_oh", True),
                ("EBIT", "ebit", False),
                ("Margen EBIT", "por_ebit", True),
                ("Gasto Fin", "gasto_fin_pro", False),
                ("Margen Gasto Fin", "por_gasto_fin", True),
                ("Ingreso Fin", "ingreso_fin_pro", False),
                ("Margen Ingreso Fin", "por_ingreso_fin", True),
                ("EBT", "ebt", False),
                ("Margen EBT", "por_ebt", True),
            ]

            if st.session_state.get("rol", "").lower() == "gerente":
                metricas = metricas_base
            else:
                metricas = metricas_base + metricas_extra

            filas = []
            for concepto, clave, es_ratio in metricas:
                ppt_val = float(ppt.get(clave, 0) or 0)
                real_val = float(real.get(clave, 0) or 0)

                # para ratios ya vienen como 0.XX -> convertir a %
                if es_ratio:
                    ppt_show = ppt_val * 100
                    real_show = real_val * 100
                    dif = real_show - ppt_show
                    var_pct = (real_show / ppt_show - 1) * 100 if ppt_show != 0 else 0
                else:
                    ppt_show = ppt_val
                    real_show = real_val
                    dif = real_show - ppt_show
                    var_pct = (real_show / ppt_show - 1) * 100 if ppt_show != 0 else 0

                filas.append({
                    "CONCEPTO": concepto if not es_ratio else f"{concepto} %".replace(" % %", " %"),
                    "PPT": ppt_show,
                    "REAL": real_show,
                    "DIF": dif,
                    "VARIACIÓN %": var_pct
                })

            df_out = pd.DataFrame(filas)

            st.subheader(f"PPT vs REAL — {proyecto_nombre}")
            st.dataframe(_tabla_resumen_style(df_out), use_container_width=True)
            return df_out

        # ---------- selector ----------
        col1, col2 = st.columns(2)
        meses_seleccionado = filtro_meses(col1, df_ppt)
        proyecto_codigo, proyecto_nombre = filtro_pro(col2)

        df_agrid = df_ppt
        tabla_variacion_pct(df_ppt, df_real, meses_seleccionado, proyecto_nombre, proyecto_codigo)
        if st.session_state.get("rol", "").lower() == "gerente":
            ventanas = ["INGRESO", "COSS", "G.ADMN"]
        else:
            ventanas = ["INGRESO", "COSS", "G.ADMN", "GASTOS FINANCIEROS", "INGRESO FINANCIERO"]

        tabs = st.tabs(ventanas)

        with tabs[0]:
            tabla_comparativa(
                "PPT", df_agrid, df_real,
                proyecto_codigo, meses_seleccionado,
                "Categoria_A", "INGRESO",
                "Tabla de Ingresos"
            )

        with tabs[1]:
            tabla_comparativa(
                "PPT", df_agrid, df_real,
                proyecto_codigo, meses_seleccionado,
                "Clasificacion_A", "COSS",
                "Tabla de COSS"
            )

        with tabs[2]:
            tabla_comparativa(
                "PPT", df_agrid, df_real,
                proyecto_codigo, meses_seleccionado,
                "Clasificacion_A", "G.ADMN",
                "Tabla de G.ADMN"
            )

        if st.session_state.get("rol", "").lower() != "gerente":
            with tabs[3]:
                tabla_comparativa(
                    "PPT", df_agrid, df_real,
                    proyecto_codigo, meses_seleccionado,
                    "Clasificacion_A", "GASTOS FINANCIEROS",
                    "Tabla de Gastos Financieros"
                )

            with tabs[4]:
                tabla_comparativa(
                    "PPT", df_agrid, df_real,
                    proyecto_codigo, meses_seleccionado,
                    "Categoria_A", "INGRESO POR REVALUACION CAMBIARIA",
                    "Tabla de Ingreso Financiero"
                )

    elif selected == "Ingresos":

        def tabla_ingresos(df_ppt, df_real, meses_seleccionado, proyectos_seleccionados):
            if not meses_seleccionado:
                st.error("Favor de seleccionar por lo menos un mes")
                return

            MESES_ORDENADOS = ["ene.", "feb.", "mar.", "abr.", "may.", "jun.", "jul.", "ago.", "sep.", "oct.", "nov.", "dic."]

            if not proyectos_seleccionados:
                st.error("Favor de seleccionar por lo menos un proyecto")
                return

            if "ESGARI" in proyectos_seleccionados:
                proyectos_ppt = df_ppt["Proyecto_A"].astype(str).unique().tolist()
                proyectos_real = df_real["Proyecto_A"].astype(str).unique().tolist()
            else:
                proyectos_ppt = [str(p) for p in proyectos_seleccionados]
                proyectos_real = [str(p) for p in proyectos_seleccionados]

            df_ppt_f = df_ppt[
                (df_ppt["Mes_A"].isin(meses_seleccionado)) &
                (df_ppt["Proyecto_A"].astype(str).isin(proyectos_ppt)) &
                (df_ppt["Categoria_A"] == "INGRESO")
            ].copy()

            df_real_f = df_real[
                (df_real["Mes_A"].isin(meses_seleccionado)) &
                (df_real["Proyecto_A"].astype(str).isin(proyectos_real)) &
                (df_real["Categoria_A"] == "INGRESO")
            ].copy()

            ppt_por_mes = (
                df_ppt_f
                .groupby("Mes_A", as_index=False)["Neto_A"]
                .sum()
                .rename(columns={"Neto_A": "PPT"})
            )

            real_por_mes = (
                df_real_f
                .groupby("Mes_A", as_index=False)["Neto_A"]
                .sum()
                .rename(columns={"Neto_A": "REAL"})
            )

            tabla = ppt_por_mes.merge(real_por_mes, on="Mes_A", how="outer").fillna(0)

            tabla["DIF"] = tabla["REAL"] - tabla["PPT"]
            tabla["%"] = tabla.apply(
                lambda r: (r["REAL"] / r["PPT"] - 1) if r["PPT"] != 0 else 0,
                axis=1
            )
            orden = {m: i for i, m in enumerate(MESES_ORDENADOS)}
            tabla["__ord"] = tabla["Mes_A"].map(orden).fillna(999).astype(int)
            tabla = tabla.sort_values("__ord").drop(columns="__ord")

            total_ppt = tabla["PPT"].sum()
            total_real = tabla["REAL"].sum()
            total_dif = total_real - total_ppt
            total_pct = (total_real / total_ppt - 1) if total_ppt != 0 else 0

            total_row = pd.DataFrame([{
                "Mes_A": "TOTAL",
                "PPT": total_ppt,
                "REAL": total_real,
                "DIF": total_dif,
                "%": total_pct
            }])

            tabla_final = pd.concat([tabla, total_row], ignore_index=True)
            BLUE = "#00112B"
            styled = (
                tabla_final.style
                .set_table_styles([
                    {"selector": "thead th",
                    "props": f"background-color: {BLUE}; color: white; font-weight: 700; font-size: 14px;"},
                    {"selector": "tbody td",
                    "props": "font-size: 13px;"},
                ])
                .format({
                    "PPT": "${:,.2f}",
                    "REAL": "${:,.2f}",
                    "DIF": "${:,.2f}",
                    "%": "{:.2%}",
                })
            )

            st.subheader("📈 Comparativa de Ingresos")
            st.dataframe(styled, use_container_width=True)

            fig = go.Figure()

            fig.add_trace(go.Scatter(
                x=tabla["Mes_A"],
                y=tabla["PPT"],
                mode="lines+markers",
                name="Ingreso PPT"
            ))

            fig.add_trace(go.Scatter(
                x=tabla["Mes_A"],
                y=tabla["REAL"],
                mode="lines+markers",
                name="Ingreso REAL"
            ))

            fig.update_layout(
                title="Ingreso PPT vs REAL",
                xaxis_title="Mes",
                yaxis_title="Ingreso",
                hovermode="x unified",
                legend_title="Tipo",
                height=420
            )

            st.plotly_chart(fig, use_container_width=True)

        col1, col2 = st.columns(2)
        meses_seleccionado = filtro_meses(col1, df_ppt)
        proyecto_codigo, proyecto_nombre = filtro_pro(col2)
        tabla_ingresos(df_ppt, df_real, meses_seleccionado, proyecto_codigo)


    elif selected == "OH":

        def tabla_oh_ppt_vs_real(df_ppt, df_real, meses_seleccionado, cecos_seleccionados):
            MESES_ORDENADOS = ["ene.", "feb.", "mar.", "abr.", "may.", "jun.", "jul.", "ago.", "sep.", "oct.", "nov.", "dic."]

            if not meses_seleccionado:
                st.error("Favor de seleccionar por lo menos un mes")
                return None

            if not cecos_seleccionados:
                st.error("Favor de seleccionar por lo menos un ceco")
                return None

            proyectos_oh = ["8002", "8004"]
            clas_oh = ["COSS", "G.ADMN"]

            df_ppt_f = df_ppt[
                (df_ppt["Mes_A"].isin(meses_seleccionado)) &
                (df_ppt["Proyecto_A"].astype(str).isin(proyectos_oh)) &
                (df_ppt["Clasificacion_A"].isin(clas_oh)) &
                (df_ppt["CeCo_A"].astype(str).isin([str(x) for x in cecos_seleccionados]))
            ].copy()

            df_real_f = df_real[
                (df_real["Mes_A"].isin(meses_seleccionado)) &
                (df_real["Proyecto_A"].astype(str).isin(proyectos_oh)) &
                (df_real["Clasificacion_A"].isin(clas_oh)) &
                (df_real["CeCo_A"].astype(str).isin([str(x) for x in cecos_seleccionados]))
            ].copy()

            ppt_por_mes = (
                df_ppt_f.groupby("Mes_A", as_index=False)["Neto_A"]
                .sum()
                .rename(columns={"Neto_A": "PPT"})
            )

            real_por_mes = (
                df_real_f.groupby("Mes_A", as_index=False)["Neto_A"]
                .sum()
                .rename(columns={"Neto_A": "REAL"})
            )

            tabla = ppt_por_mes.merge(real_por_mes, on="Mes_A", how="outer").fillna(0)
            tabla["DIF"] = tabla["REAL"] - tabla["PPT"]
            tabla["%"] = tabla.apply(lambda r: (r["REAL"] / r["PPT"] - 1) if r["PPT"] != 0 else 0, axis=1)

            orden = {m: i for i, m in enumerate(MESES_ORDENADOS)}
            tabla["__ord"] = tabla["Mes_A"].map(orden).fillna(999).astype(int)
            tabla = tabla.sort_values("__ord").drop(columns="__ord")

            total_ppt = float(tabla["PPT"].sum())
            total_real = float(tabla["REAL"].sum())
            total_dif = total_real - total_ppt
            total_pct = (total_real / total_ppt - 1) if total_ppt != 0 else 0

            total_row = pd.DataFrame([{
                "Mes_A": "TOTAL",
                "PPT": total_ppt,
                "REAL": total_real,
                "DIF": total_dif,
                "%": total_pct
            }])

            tabla_final = pd.concat([tabla, total_row], ignore_index=True)

            # ✅ SOLO FORMATO (misma lógica)
            BLUE = "#00112B"
            styled = (
                tabla_final.style
                .set_table_styles([
                    {"selector": "thead th",
                    "props": f"background-color: {BLUE}; color: white; font-weight: 700; font-size: 14px;"},
                    {"selector": "tbody td", "props": "font-size: 13px;"},
                ])
                .format({
                    "PPT": "${:,.2f}",
                    "REAL": "${:,.2f}",
                    "DIF": "${:,.2f}",
                    "%": "{:.2%}",
                })
            )

            st.subheader("📌 OH — PPT vs REAL")
            st.dataframe(styled, use_container_width=True)

            # ✅ Gráfico (PPT vs REAL por mes; sin cambiar cálculos)
            fig = go.Figure()
            fig.add_trace(go.Bar(x=tabla["Mes_A"], y=tabla["PPT"], name="PPT"))
            fig.add_trace(go.Bar(x=tabla["Mes_A"], y=tabla["REAL"], name="REAL"))
            fig.update_layout(
                title="OH PPT vs REAL",
                xaxis_title="Mes",
                yaxis_title="Monto",
                barmode="group",
                height=420,
                legend_title="Tipo",
            )
            st.plotly_chart(fig, use_container_width=True)

            return tabla_final
        def agrid_oh_con_totales(df, filtro_col, filtro_val):
            """
            AgGrid con totales por Categoría y por Cuenta (columna extra),
            aplicable a COSS / G.ADMN / GASTOS FINANCIEROS / INGRESO FINANCIERO (según filtro).
            - filtro_col: "Clasificacion_A" o "Categoria_A"
            - filtro_val: e.g. "COSS" o "G.ADMN" o "GASTOS FINANCIEROS" o "INGRESO POR REVALUACION CAMBIARIA" (etc.)
            """
            df = df.copy()
            df = df[df[filtro_col] == filtro_val]
            df_g = (
                df.groupby(["Categoria_A", "Cuenta_A", "Cuenta_Nombre_A"], as_index=False)
                .agg({"Neto_A": "sum"})
            )
            tot_cuenta = (
                df_g.groupby(["Cuenta_A", "Cuenta_Nombre_A"], as_index=False)["Neto_A"]
                    .sum()
                    .rename(columns={"Neto_A": "Total Cuenta"})
            )
            df_g = df_g.merge(tot_cuenta, on=["Cuenta_A", "Cuenta_Nombre_A"], how="left")

            currency_formatter = JsCode("""
            function(params) {
                if (params.value === null || params.value === undefined) return "";
                return new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN' }).format(params.value);
            }
            """)

            gb = GridOptionsBuilder.from_dataframe(df_g)
            gb.configure_default_column(resizable=True, sortable=True, filter=True)
            gb.configure_column("Categoria_A", rowGroup=True, hide=True)
            gb.configure_column("Cuenta_A", header_name="Cuenta", pinned="left")
            gb.configure_column("Cuenta_Nombre_A", header_name="Cuenta Nombre", pinned="left")
            gb.configure_column("Neto_A", header_name="sum(Neto_A)", type=["numericColumn"], aggFunc="sum", valueFormatter=currency_formatter)
            gb.configure_column("Total Cuenta", header_name="sum(Total Cuenta)", type=["numericColumn"], aggFunc="sum", valueFormatter=currency_formatter)

            grid_options = gb.build()
            grid_options.update({
                "groupDisplayType": "groupRows",
                "groupDefaultExpanded": 1,
                "suppressAggFuncInHeader": False
            })

            AgGrid(
                df_g,
                gridOptions=grid_options,
                enable_enterprise_modules=True,
                allow_unsafe_jscode=True,
                fit_columns_on_grid_load=True,
                height=520,
                theme="streamlit",
                key=f"agrid_oh_totales_{filtro_col}_{filtro_val}"
            )

        col1, col2 = st.columns(2)
        meses_seleccionado = filtro_meses(col1, df_ppt)
        ceco_codigo, ceco_nombre = filtro_ceco(col2)

        tabla_oh_ppt_vs_real(df_ppt, df_real, meses_seleccionado, ceco_codigo)

        proyectos_oh = ["8002", "8004"]

        if meses_seleccionado and ceco_codigo:
            df_agrid_oh = df_ppt[
                (df_ppt["Proyecto_A"].astype(str).isin(proyectos_oh)) &
                (df_ppt["CeCo_A"].astype(str).isin([str(x) for x in ceco_codigo]))
            ].copy()

            df_actual_oh = df_real[
                (df_real["Proyecto_A"].astype(str).isin(proyectos_oh)) &
                (df_real["CeCo_A"].astype(str).isin([str(x) for x in ceco_codigo]))
            ].copy()

            ventanas = ["COSS", "G.ADMN"]
            tabs = st.tabs(ventanas)

            with tabs[0]:
                tabla_comparativa(
                    "PPT",
                    df_agrid_oh,
                    df_actual_oh,
                    proyectos_oh,
                    meses_seleccionado,
                    "Clasificacion_A",
                    "COSS",
                    "OH - Tabla COSS"
                )
                st.markdown("#### AgGrid (COSS) — Totales por Categoría y Cuenta")
                agrid_oh_con_totales(df_actual_oh, filtro_col="Clasificacion_A", filtro_val="COSS")

            with tabs[1]:
                tabla_comparativa(
                    "PPT",
                    df_agrid_oh,
                    df_actual_oh,
                    proyectos_oh,
                    meses_seleccionado,
                    "Clasificacion_A",
                    "G.ADMN",
                    "OH - Tabla G.ADMN"
                )
                st.markdown("#### AgGrid (G.ADMN) — Totales por Categoría y Cuenta")
                agrid_oh_con_totales(df_actual_oh, filtro_col="Clasificacion_A", filtro_val="G.ADMN")


    elif selected == "Departamentos":
        def tabla_departamentos(df_ppt, df_real, meses_seleccionado, cecos_seleccionados, cecos):
            if not meses_seleccionado:
                st.error("Favor de seleccionar por lo menos un mes")
                return None

            if not cecos_seleccionados:
                st.error("Favor de seleccionar por lo menos un ceco")
                return None

            proyectos_oh = ["8002", "8004"]
            clas_oh = ["COSS", "G.ADMN"]

            df_ppt = df_ppt.copy()
            df_real = df_real.copy()

            df_ppt["Proyecto_A"] = df_ppt["Proyecto_A"].astype(str).str.strip()
            df_real["Proyecto_A"] = df_real["Proyecto_A"].astype(str).str.strip()
            df_ppt["CeCo_A"] = df_ppt["CeCo_A"].astype(str).str.strip()
            df_real["CeCo_A"] = df_real["CeCo_A"].astype(str).str.strip()

            cecos_sel = [str(x) for x in cecos_seleccionados]

            df_ppt_f = df_ppt[
                (df_ppt["Mes_A"].isin(meses_seleccionado)) &
                (df_ppt["Proyecto_A"].isin(proyectos_oh)) &
                (df_ppt["Clasificacion_A"].isin(clas_oh)) &
                (df_ppt["CeCo_A"].isin(cecos_sel))
            ].copy()

            df_real_f = df_real[
                (df_real["Mes_A"].isin(meses_seleccionado)) &
                (df_real["Proyecto_A"].isin(proyectos_oh)) &
                (df_real["Clasificacion_A"].isin(clas_oh)) &
                (df_real["CeCo_A"].isin(cecos_sel))
            ].copy()

            ppt_por_ceco = (
                df_ppt_f.groupby("CeCo_A", as_index=False)["Neto_A"]
                .sum()
                .rename(columns={"Neto_A": "PPT"})
            )

            real_por_ceco = (
                df_real_f.groupby("CeCo_A", as_index=False)["Neto_A"]
                .sum()
                .rename(columns={"Neto_A": "REAL"})
            )

            tabla = ppt_por_ceco.merge(real_por_ceco, on="CeCo_A", how="outer").fillna(0)
            tabla["DIF"] = tabla["REAL"] - tabla["PPT"]
            tabla["%"] = np.where(tabla["PPT"] != 0, (tabla["REAL"] / tabla["PPT"]) - 1, 0)

            # ---- map CeCo nombre ----
            cecos_map = cecos.copy()
            cecos_map["ceco"] = cecos_map["ceco"].astype(str).str.strip()
            cecos_map["nombre"] = cecos_map["nombre"].astype(str).str.strip()

            tabla = tabla.merge(
                cecos_map.rename(columns={"ceco": "CeCo_A", "nombre": "ceco"})[["CeCo_A", "ceco"]],
                on="CeCo_A",
                how="left"
            )
            tabla["ceco"] = tabla["ceco"].fillna(tabla["CeCo_A"])

            tabla = tabla[["ceco", "REAL", "PPT", "DIF", "%"]]

            # ---- total ----
            total_ppt = float(tabla["PPT"].sum())
            total_real = float(tabla["REAL"].sum())
            total_dif = total_real - total_ppt
            total_pct = (total_real / total_ppt - 1) if total_ppt != 0 else 0

            total_row = pd.DataFrame([{
                "ceco": "TOTAL",
                "REAL": total_real,
                "PPT": total_ppt,
                "DIF": total_dif,
                "%": total_pct
            }])

            tabla_final = pd.concat([tabla, total_row], ignore_index=True)

            def color_fila(row):
                if row["ceco"] == "TOTAL":
                    return ["background-color: #1f4e79; color: white; font-weight: bold"] * len(row)
                v = row["%"]
                if v >= 0:
                    bg = "#92D050"
                elif v >= -0.05:
                    bg = "#FFD966"
                else:
                    bg = "#FF0000"
                return [f"background-color: {bg}; color: black"] * len(row)

            styled = (
                tabla_final.style
                .apply(color_fila, axis=1)
                .format({
                    "REAL": "${:,.2f}",
                    "PPT": "${:,.2f}",
                    "DIF": "${:,.2f}",
                    "%": "{:.2%}",
                })
            )

            st.subheader("Departamentos")
            st.dataframe(styled, use_container_width=True)

            return tabla_final
        col1, col2 = st.columns(2)
        meses_seleccionado = filtro_meses(col1, df_ppt)
        ceco_codigo, ceco_nombre = filtro_ceco(col2)

        tabla_final = tabla_departamentos(df_ppt, df_real, meses_seleccionado, ceco_codigo, ceco_nombre)
        if tabla_final is not None and not tabla_final.empty:

            ventanas = ["Grafico PPT vs Real", "Grafico PPT", "Grafico Real"]
            tabs = st.tabs(ventanas)

            tabla_graf = (tabla_final[tabla_final["ceco"] != "TOTAL"].sort_values("DIF", ascending=False).copy())

            with tabs[0]:
                if not tabla_graf.empty:
                    fig = go.Figure()
                    fig.add_bar(x=tabla_graf["ceco"], y=tabla_graf["PPT"], name="PPT")
                    fig.add_bar(x=tabla_graf["ceco"], y=tabla_graf["REAL"], name="REAL")
                    fig.update_layout(
                        title="PPT vs REAL por Departamento",
                        xaxis_title="Departamento",
                        yaxis_title="Monto",
                        barmode="group",
                        height=450,
                        legend_title="Tipo",
                        xaxis_tickangle=-25
                    )
                    st.plotly_chart(fig, use_container_width=True)

            with tabs[1]:
                if not tabla_graf.empty:
                    fig = go.Figure()
                    fig.add_bar(x=tabla_graf["ceco"], y=tabla_graf["PPT"], name="PPT")
                    fig.update_layout(
                        title="PPT por Departamento",
                        xaxis_title="Departamento",
                        yaxis_title="Monto PPT",
                        height=450,
                        xaxis_tickangle=-25
                    )
                    st.plotly_chart(fig, use_container_width=True)

            with tabs[2]:
                if not tabla_graf.empty:
                    fig = go.Figure()
                    fig.add_bar(x=tabla_graf["ceco"], y=tabla_graf["REAL"], name="REAL")
                    fig.update_layout(
                        title="REAL por Departamento",
                        xaxis_title="Departamento",
                        yaxis_title="Monto REAL",
                        height=450,
                        xaxis_tickangle=-25
                    )
                    st.plotly_chart(fig, use_container_width=True)
            with st.expander("COSS y G.ADMN", expanded=False):

                if not meses_seleccionado or not ceco_codigo:
                    st.info("Selecciona meses y CeCo para ver el detalle.")
                else:
                    proyectos_oh = ["8002", "8004"]
                    df_agrid_oh = df_ppt[
                        (df_ppt["Proyecto_A"].astype(str).isin(proyectos_oh)) &
                        (df_ppt["CeCo_A"].astype(str).isin([str(x) for x in ceco_codigo]))
                    ].copy()

                    df_actual_oh = df_real[
                        (df_real["Proyecto_A"].astype(str).isin(proyectos_oh)) &
                        (df_real["CeCo_A"].astype(str).isin([str(x) for x in ceco_codigo]))
                    ].copy()

                    st.markdown("### 🔹 COSS")
                    tabla_comparativa(
                        tipo_com="PPT",
                        df_agrid=df_agrid_oh,
                        df_ppt=df_actual_oh,
                        proyecto_codigo=proyectos_oh,
                        meses_seleccionado=meses_seleccionado,
                        clasificacion="Clasificacion_A",
                        categoria="COSS",
                        titulo="COSS"
                    )

                    st.markdown("---")

                    st.markdown("### 🔹 G.ADMN")
                    tabla_comparativa(
                        tipo_com="PPT",
                        df_agrid=df_agrid_oh,
                        df_ppt=df_actual_oh,
                        proyecto_codigo=proyectos_oh,
                        meses_seleccionado=meses_seleccionado,
                        clasificacion="Clasificacion_A",
                        categoria="G.ADMN",
                        titulo="G.ADMN"
                    )

    elif selected == "Consulta":

        def tabla_Consultas(df_ppt, df_real, meses_seleccionado, cecos_seleccionados, proyectos_seleccionados):
            if not meses_seleccionado:
                st.error("Favor de seleccionar por lo menos un mes")
                return None
            if not cecos_seleccionados:
                st.error("Favor de seleccionar por lo menos un ceco")
                return None
            if not proyectos_seleccionados:
                st.error("Favor de seleccionar por lo menos un proyecto")
                return None

            df_ppt = df_ppt.copy()
            df_real = df_real.copy()

            df_ppt["Cuenta_A"] = df_ppt["Cuenta_A"].astype(str).str.strip()
            df_real["Cuenta_A"] = df_real["Cuenta_A"].astype(str).str.strip()
            df_ppt["Cuenta_Nombre_A"] = df_ppt["Cuenta_Nombre_A"].astype(str).str.strip()
            df_real["Cuenta_Nombre_A"] = df_real["Cuenta_Nombre_A"].astype(str).str.strip()

            cuentas_df = pd.concat([
                df_ppt[["Cuenta_A", "Cuenta_Nombre_A"]],
                df_real[["Cuenta_A", "Cuenta_Nombre_A"]]
            ]).drop_duplicates().sort_values("Cuenta_Nombre_A")

            opciones_cuenta = ["TODAS"] + cuentas_df["Cuenta_Nombre_A"].tolist()

            cuenta_seleccionada = st.selectbox(
                "Selecciona una cuenta",
                opciones_cuenta,
                key="consulta_cuenta_select"
            )

            df_ppt_f = df_ppt[
                (df_ppt["Mes_A"].isin(meses_seleccionado)) &
                (df_ppt["CeCo_A"].astype(str).isin([str(x) for x in cecos_seleccionados])) &
                (df_ppt["Proyecto_A"].astype(str).isin([str(x) for x in proyectos_seleccionados]))
            ].copy()

            df_real_f = df_real[
                (df_real["Mes_A"].isin(meses_seleccionado)) &
                (df_real["CeCo_A"].astype(str).isin([str(x) for x in cecos_seleccionados])) &
                (df_real["Proyecto_A"].astype(str).isin([str(x) for x in proyectos_seleccionados]))
            ].copy()

            if cuenta_seleccionada != "TODAS":
                df_ppt_f = df_ppt_f[df_ppt_f["Cuenta_Nombre_A"] == cuenta_seleccionada]
                df_real_f = df_real_f[df_real_f["Cuenta_Nombre_A"] == cuenta_seleccionada]

            ppt_resumen = (
                df_ppt_f.groupby("Cuenta_Nombre_A", as_index=False)["Neto_A"]
                .sum()
                .rename(columns={"Neto_A": "PPT"})
            )
            real_resumen = (
                df_real_f.groupby("Cuenta_Nombre_A", as_index=False)["Neto_A"]
                .sum()
                .rename(columns={"Neto_A": "REAL"})
            )

            tabla = ppt_resumen.merge(real_resumen, on="Cuenta_Nombre_A", how="outer").fillna(0)
            tabla["DIF"] = tabla["REAL"] - tabla["PPT"]
            tabla["%"] = np.where(tabla["PPT"] != 0, (tabla["REAL"] / tabla["PPT"]) - 1, 0)

            st.subheader("Consulta por Cuenta")
            st.dataframe(
                tabla.style.format({
                    "PPT": "${:,.2f}",
                    "REAL": "${:,.2f}",
                    "DIF": "${:,.2f}",
                    "%": "{:.2%}"
                }),
                use_container_width=True
            )

            if not tabla.empty:
                fig = go.Figure()
                fig.add_bar(x=tabla["Cuenta_Nombre_A"], y=tabla["PPT"], name="PPT")
                fig.add_bar(x=tabla["Cuenta_Nombre_A"], y=tabla["REAL"], name="REAL")
                fig.update_layout(
                    title="PPT vs REAL por Cuenta",
                    xaxis_title="Cuenta",
                    yaxis_title="Monto",
                    barmode="group",
                    height=420,
                    legend_title="Tipo",
                    xaxis_tickangle=-30
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Sin datos con los filtros seleccionados.")

            return tabla 
        
        col1, col2, col3 = st.columns(3)
        meses_seleccionado = filtro_meses(col1, df_ppt)
        ceco_codigo, ceco_nombre = filtro_ceco(col2)
        proyecto_codigo, proyecto_nombre = filtro_pro(col3)

        tabla_Consultas(df_ppt, df_real, meses_seleccionado, ceco_codigo, proyecto_codigo)

        
    elif selected == "Meses PPT":
        def mostrar_meses_ppt(df_ppt):
            meses_disponibles = df_ppt["Mes_A"].unique().tolist()
            codigo_pro, pro = filtro_pro(st)
            ceco_codi, ceco_nomb = filtro_ceco(st)
            df_ppt["CeCo_A"] = df_ppt["CeCo_A"].astype(str)
            if ceco_nomb != "ESGARI":
                df_ppt = df_ppt[df_ppt["CeCo_A"].isin(ceco_codi)]
            meses_ordenados = ["ene.", "feb.", "mar.", "abr.", "may.", "jun.",
                    "jul.", "ago.", "sep.", "oct.", "nov.", "dic."]

            meses_disponibles = [mes for mes in meses_ordenados if mes in df_ppt["Mes_A"].unique()]
            meses_filtrados = st.multiselect(
                "Selecciona los meses que deseas incluir:",
                options=meses_disponibles,
                default=meses_disponibles,
                key="filtro_meses_est_res"
            )
            if len(meses_filtrados) <2:
                st.error("Selecionar dos meses o más!")
            else:

                # --- Función principal para generar el estado de resultado mensual ---
                def estado_resultado_por_mes(df_2025, proyecto_nombre, proyecto_codigo, lista_proyectos):
                    meses_ordenados = ["ene.", "feb.", "mar.", "abr.", "may.", "jun.", "jul.", "ago.", "sep.", "oct.", "nov.", "dic."]

                    meses_disponibles = [mes for mes in meses_ordenados if mes in meses_filtrados]
                    resultado_por_mes = {}

                    for mes in meses_disponibles:
                        estado_mes = estado_resultado(
                            df_2025,
                            meses_seleccionado=[mes],
                            proyecto_nombre=proyecto_nombre,
                            proyecto_codigo=proyecto_codigo,
                            lista_proyectos=lista_proyectos
                        )
                        resultado_por_mes[mes] = estado_mes

                    df_resultado = pd.DataFrame(resultado_por_mes)

                    # Diccionario estricto: porcentaje -> métrica base
                    porcentajes_base = {
                        "porcentaje_ingresos": "ingreso_proyecto",
                        "por_patio": "patio_pro",
                        "por_coss": "coss_total",
                        "por_utilidad_bruta": "utilidad_bruta",
                        "por_gadmn": "gadmn_pro",
                        "por_utilidad_operativa": "utilidad_operativa",
                        "por_oh": "oh_pro",
                        "por_ebit": "ebit",
                        "por_gasto_fin": "gasto_fin_pro",
                        "por_ingreso_fin": "ingreso_fin_pro",
                        "por_resultado_fin": "resultado_fin",
                        "por_ebt": "ebt"
                    }

                    # Función para calcular columna Total
                    def calcular_total(row):
                        if row.name in porcentajes_base:
                            base_row = porcentajes_base[row.name]
                            ingreso_total = df_resultado.loc["ingreso_proyecto"].sum(skipna=True)
                            if base_row in df_resultado.index and ingreso_total != 0:
                                base_total = df_resultado.loc[base_row].sum(skipna=True)
                                return base_total / ingreso_total
                            else:
                                return np.nan
                        else:
                            return row.sum(skipna=True)

                    # Agregar columna Total
                    df_resultado["Total"] = df_resultado.apply(calcular_total, axis=1)

                    # Agregar columna Promedio
                    columnas_meses = [col for col in df_resultado.columns if col != "Total"]
                    df_resultado["Promedio"] = df_resultado[columnas_meses].mean(axis=1, skipna=True)
                    return df_resultado

                # Ejecutar función
                tabla_mensual = estado_resultado_por_mes(df_ppt, pro, codigo_pro, list_pro)

                # Diccionario para formateo
                porcentajes_base = {
                    "porcentaje_ingresos": "ingreso_proyecto",
                    "por_patio": "patio_pro",
                    "por_coss": "coss_total",
                    "por_utilidad_bruta": "utilidad_bruta",
                    "por_gadmn": "gadmn_pro",
                    "por_utilidad_operativa": "utilidad_operativa",
                    "por_oh": "oh_pro",
                    "por_ebit": "ebit",
                    "por_gasto_fin": "gasto_fin_pro",
                    "por_ingreso_fin": "ingreso_fin_pro",
                    "por_resultado_fin": "resultado_fin",
                    "por_ebt": "ebt"
                }

                # Crear copia formateada
                tabla_formateada = tabla_mensual.copy()

                for row in tabla_formateada.index:
                    if "por" in row.lower() or row.startswith("%"):
                        tabla_formateada.loc[row] = tabla_formateada.loc[row].apply(lambda x: f"{x:.2%}" if pd.notnull(x) else "")
                    else:
                        tabla_formateada.loc[row] = tabla_formateada.loc[row].apply(lambda x: f"${x:,.0f}" if pd.notnull(x) else "")

                # Renombrar filas
                nombres_filas = {
                    "ingreso_proyecto": "Ingresos",
                    "patio_pro": "Patio",            
                    "coss_total": "COSS",
                    "utilidad_bruta": "Utilidad Bruta",
                    "gadmn_pro": "Gastos Admin.",
                    "utilidad_operativa": "Utilidad Operativa",
                    "oh_pro": "OH",
                    "ebit": "EBIT",
                    "gasto_fin_pro": "Gastos Financieros",
                    "oh_pro_gfin": "Gasto financiero OH",
                    "ingreso_fin_pro": "Ingresos Financieros",
                    "ebt": "EBT",
                    "porcentaje_ingresos": "% de Ingresos",
                    "por_patio": "% Patio",
                    "por_coss": "% COSS",
                    "por_utilidad_bruta": "% Utilidad Bruta",
                    "por_gadmn": "% G. Admin",
                    "por_utilidad_operativa": "% Utilidad Operativa",
                    "por_oh": "% Overhead",
                    "por_ebit": "% EBIT",
                    "por_gasto_fin": "% Gasto Financiero",
                    "por_ingreso_fin": "% Ingreso Financiero",
                    "oh_pro_ifin": "Ingreso OH",
                    "por_resultado_fin": "% Resultado Financiero",
                    "por_ebt": "% EBT",
                    
                }
                tabla_mensual_renombrada = tabla_formateada.rename(index=nombres_filas)
                tabla_mensual_renombrada = tabla_mensual_renombrada.drop(
                    index=["coss_pro", "mal_coss", "mal_gadmn", "mal_gfin", "mal_ifin", "resultado_fin", "% de Ingresos"],
                    errors='ignore'
                )
                if st.session_state["rol"] == "gerente":
                    tabla_mensual_renombrada = tabla_mensual_renombrada.drop(
                        index=["OH", "EBIT", "Gastos Financieros", "Gasto financiero OH", "Ingresos Financieros", "EBT", "% Overhead", "% EBIT", "% Gasto Financiero", "% Ingreso Financiero", "Ingreso OH", "% Resultado Financiero", "% EBT"],
                        errors='ignore'
                    )    

                # --- Estilo visual profesional para tabla mensual ---
                def generar_tabla_con_estilo_mensual(df):
                    df_reset = df.reset_index().rename(columns={"index": "Concepto"})
                    filas_porcentaje = [nombre for nombre in df_reset["Concepto"] if nombre.startswith("%") or "por" in nombre.lower()]

                    def aplicar_estilos(row):
                        if row["Concepto"] == "Promedio Mensual":
                            return ['background-color: #cccccc; color: black; font-weight: bold;' for _ in row]
                        elif row["Concepto"] in filas_porcentaje:
                            return ['background-color: #00112B; color: white;' for _ in row]
                        else:
                            color_fondo = '#ffffff' if row.name % 2 == 0 else '#f2f2f2'
                            return [f'background-color: {color_fondo}; color: black;' for _ in row]

                    estilos_header = [
                        {'selector': 'thead th', 'props': 'background-color: #00112B; color: white; font-weight: bold; font-size: 14px;'}
                    ]

                    html = (
                        df_reset.style
                        .apply(aplicar_estilos, axis=1)
                        .set_table_styles(estilos_header)
                        .set_properties(**{'font-size': '12px', 'text-align': 'right'})
                        .hide(axis='index')
                        .to_html()
                    )

                    responsive_html = f'<div style="overflow-x: auto; width: 100%;">{html}</div>'
                    return responsive_html

                # Mostrar en Streamlit
                st.write(f"### Estado de Resultado por Mes '{pro}'")
                tabla_html = generar_tabla_con_estilo_mensual(tabla_mensual_renombrada)
                st.markdown(tabla_html, unsafe_allow_html=True)
                meses_ordenados = ["ene.", "feb.", "mar.", "abr.", "may.", "jun.",
                                "jul.", "ago.", "sep.", "oct.", "nov.", "dic."]

                meses_disponibles = [mes for mes in meses_ordenados if mes in meses_filtrados]

                df_meses = df_ppt[df_ppt["Proyecto_A"].isin(codigo_pro)]
                df_meses = df_meses[~(df_meses["Clasificacion_A"].isin(["IMPUESTOS", "OTROS INGRESOS"]))]
                if st.session_state["rol"] == "gerente":
                    df_meses = df_meses[~(df_meses["Clasificacion_A"].isin(["GASTOS FINANCIEROS"]))]
                df_meses = df_meses.groupby(
                    ["Clasificacion_A", "Categoria_A", "Cuenta_Nombre_A", "Mes_A"],
                    as_index=False
                )["Neto_A"].sum()

                df_pivot = df_meses.pivot_table(
                    index=["Clasificacion_A", "Categoria_A", "Cuenta_Nombre_A"],
                    columns="Mes_A",
                    values="Neto_A",
                    aggfunc="sum"
                )
                for mes in meses_disponibles:
                    if mes not in df_pivot.columns:
                        df_pivot[mes] = 0
                df_pivot = df_pivot[meses_disponibles]
                df_pivot = df_pivot.reset_index().fillna(0)
                columnas_mensuales = [col for col in df_pivot.columns if col not in ["Clasificacion_A", "Categoria_A", "Cuenta_Nombre_A"]]
                df_pivot["Total"] = df_pivot[columnas_mensuales].sum(axis=1)
                df_pivot["Promedio"] = df_pivot[columnas_mensuales].mean(axis=1)
                gb = GridOptionsBuilder.from_dataframe(df_pivot)
                gb.configure_column("Clasificacion_A", rowGroup=True, hide=True)
                gb.configure_column("Categoria_A", rowGroup=True, hide=True)
                gb.configure_column("Cuenta_Nombre_A", pinned='left')
                currency_formatter = JsCode("""
                    function(params) {
                        if (params.value === 0 || params.value === null) {
                            return "$0.00";
                        }
                        return new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN' }).format(params.value);
                    }
                """)

                # Aplicar formato visual con el formateador JS
                for col in df_pivot.columns:
                    if col not in ["Clasificacion_A", "Categoria_A", "Cuenta_Nombre_A"]:
                        gb.configure_column(
                            col,
                            type=["numericColumn", "numberColumnFilter", "customNumericFormat"],
                            aggFunc="sum",
                            valueFormatter=currency_formatter,
                            cellStyle={'textAlign': 'right'}
                        )

                gridOptions = gb.build()

                # Mostrar en Streamlit
                st.write("### Tabla Clasificación, Categoría y Cuenta")
                AgGrid(
                    df_pivot,
                    gridOptions=gridOptions,
                    enable_enterprise_modules=True,
                    fit_columns_on_grid_load=False,
                    allow_unsafe_jscode=True,
                    domLayout='normal',
                    height=600
                )
        mostrar_meses_ppt(df_ppt)
        
    elif selected == "Variaciones":
        meses_ordenados = ["ene.", "feb.", "mar.", "abr.", "may.", "jun.", "jul.", "ago.", "sep.", "oct.", "nov.", "dic."]
        meses_disponibles = [m for m in meses_ordenados if (m in df_ppt["Mes_A"].unique()) or (m in df_real["Mes_A"].unique())]

        meses_sel = st.multiselect(
            "Selecciona mes(es):",
            options=meses_disponibles,
            default=meses_disponibles[-1:] if meses_disponibles else [],
            key="cmp_meses_excel"
        )
        if not meses_sel:
            st.error("Favor de seleccionar por lo menos un mes.")
            st.stop()
        col1, col2, col3 = st.columns(3)
        meses_seleccionado = filtro_meses(col1, df_ppt)
        proyecto_codigo, proyecto_nombre = filtro_pro(col2)
        ceco_codigo, ceco_nombre = filtro_ceco(col3)

        seccion_analisis_por_clasificacion(df_ppt, df_real, ingreso, meses_seleccionado, proyecto_codigo, proyecto_nombre, "COSS", ceco_codigo, ceco_nombre)
        seccion_analisis_especial_porcentual(df_ppt, df_real, ingreso, meses_seleccionado, proyecto_codigo, proyecto_nombre, ceco_codigo, ceco_nombre, patio, "Patio")
        seccion_analisis_por_clasificacion(df_ppt, df_real, ingreso, meses_seleccionado, proyecto_codigo, proyecto_nombre, "G.ADMN", ceco_codigo, ceco_nombre)

        if st.session_state["rol"] == "admin":
            seccion_analisis_por_clasificacion(df_ppt, df_real, ingreso, meses_seleccionado, proyecto_codigo, proyecto_nombre, "GASTOS FINANCIEROS", ceco_codigo, ceco_nombre)
            seccion_analisis_especial_porcentual(df_ppt, df_real, ingreso, meses_seleccionado, proyecto_codigo, proyecto_nombre, ceco_codigo, ceco_nombre, oh, "OH")


    elif selected == "Comparativa":

        st.subheader("Comparativa de Ingresos")

        meses_ordenados = ["ene.", "feb.", "mar.", "abr.", "may.", "jun.", "jul.", "ago.", "sep.", "oct.", "nov.", "dic."]
        meses_disponibles = [m for m in meses_ordenados if (m in df_ppt["Mes_A"].unique()) or (m in df_real["Mes_A"].unique())]

        meses_sel = st.multiselect(
            "Selecciona mes(es):",
            options=meses_disponibles,
            default=meses_disponibles[-1:] if meses_disponibles else [],
            key="cmp_meses_excel"
        )
        if not meses_sel:
            st.error("Favor de seleccionar por lo menos un mes.")
            st.stop()

        proyectos_local = proyectos.copy()
        proyectos_local["proyectos"] = proyectos_local["proyectos"].astype(str).str.strip()
        proyectos_local["nombre"] = proyectos_local["nombre"].astype(str).str.strip()

        allowed = [str(x).strip() for x in st.session_state.get("proyectos", [])]
        if allowed == ["ESGARI"]:
            df_visibles = proyectos_local.copy()
        else:
            df_visibles = proyectos_local[proyectos_local["proyectos"].isin(allowed)].copy()
        excluir = {"8002", "8003", "8004"}
        df_visibles = df_visibles[~df_visibles["proyectos"].astype(str).isin(excluir)].copy()

        df_ppt_ing = df_ppt[(df_ppt["Mes_A"].isin(meses_sel)) & (df_ppt["Categoria_A"] == "INGRESO")].copy()
        df_real_ing = df_real[(df_real["Mes_A"].isin(meses_sel)) & (df_real["Categoria_A"] == "INGRESO")].copy()

        df_ppt_ing["Proyecto_A"] = df_ppt_ing["Proyecto_A"].astype(str).str.strip()
        df_real_ing["Proyecto_A"] = df_real_ing["Proyecto_A"].astype(str).str.strip()

        nombres = df_visibles["nombre"].tolist()
        codigos = df_visibles["proyectos"].tolist()

        nombre_por_codigo = dict(zip(codigos, nombres))

        real_por_proy = {nombre_por_codigo[c]: float(df_real_ing.loc[df_real_ing["Proyecto_A"] == c, "Neto_A"].sum()) for c in codigos}
        ppt_por_proy  = {nombre_por_codigo[c]: float(df_ppt_ing.loc[df_ppt_ing["Proyecto_A"] == c, "Neto_A"].sum()) for c in codigos}

        inc_por_proy = {}
        for n in nombres:
            ppt_v = ppt_por_proy.get(n, 0.0)
            real_v = real_por_proy.get(n, 0.0)
            inc_por_proy[n] = (real_v / ppt_v - 1) if ppt_v != 0 else 0.0

        tabla_excel = pd.DataFrame(
            {
                **{n: [real_por_proy.get(n, 0.0), ppt_por_proy.get(n, 0.0), inc_por_proy.get(n, 0.0)] for n in nombres}
            },
            index=["YTD REAL", "PPT", "INCREMENTO %"]
        )

        st.markdown("Tabla")
        st.dataframe(
            tabla_excel.style
            .format(
                {col: "${:,.0f}" for col in tabla_excel.columns},
                subset=pd.IndexSlice[["YTD REAL", "PPT"], :]
            )
            .format(
                {col: "{:.2%}" for col in tabla_excel.columns},
                subset=pd.IndexSlice[["INCREMENTO %"], :]
            ),
            use_container_width=True
        )

        x = nombres
        y_real = [real_por_proy.get(n, 0.0) for n in x]
        y_ppt  = [ppt_por_proy.get(n, 0.0) for n in x]
        y_inc  = [inc_por_proy.get(n, 0.0) for n in x]

        fig = go.Figure()
        fig.add_bar(x=x, y=y_real, name="YTD REAL")
        fig.add_bar(x=x, y=y_ppt,  name="PPT")

        # Etiquetas de incremento %
        for i, n in enumerate(x):
            top = max(y_real[i], y_ppt[i])
            fig.add_annotation(
                x=n,
                y=top * 1.08 if top != 0 else 0,
                text=f"{y_inc[i]*100:,.2f}%",
                showarrow=False
            )

        fig.update_layout(
            title=f"Ingresos",
            xaxis_title="Proyecto",
            yaxis_title="MXN",
            barmode="group",
            height=520,
            hovermode="x unified",
            xaxis_tickangle=-25
        )

        st.markdown("### 📈 Gráfico de Ingresos")
        st.plotly_chart(fig, use_container_width=True)



    elif selected == "Objetivos":
        objetivo_uo = {
            "ARRAYANES": 0.24,
            "CENTRAL": 0.29,
            "CHALCO": 0.24,
            "CONTINENTAL.": 0.30,
            "FLEX DEDICADO": 0.27,
            "FLEX SPOT": 0.24,
            "INTERNACIONAL FWD": 0.24,
            "WH": 0.21,
            "MANZANILLO.": 0.25,
            "BAJIO": 0.26,
            "ESGARI": 0.25
        }

        meses_ordenados = ["ene.", "feb.", "mar.", "abr.", "may.", "jun.", "jul.", "ago.", "sep.", "oct.", "nov.", "dic."]
        meses_disponibles = [
            m for m in meses_ordenados
            if (m in df_ppt["Mes_A"].unique()) or (m in df_real["Mes_A"].unique())
        ]

        meses_sel = st.multiselect(
            "Selecciona mes(es):",
            options=meses_disponibles,
            default=meses_disponibles[-1:] if meses_disponibles else [],
            key="cmp_meses_uo_manual"
        )

        if not meses_sel:
            st.error("Favor de seleccionar por lo menos un mes.")
            st.stop()

        proyectos_local = proyectos.copy()
        proyectos_local["proyectos"] = proyectos_local["proyectos"].astype(str).str.strip()
        proyectos_local["nombre"] = proyectos_local["nombre"].astype(str).str.strip()

        allowed = [str(x).strip() for x in st.session_state.get("proyectos", [])]

        if allowed == ["ESGARI"]:
            df_visibles = proyectos_local.copy()
        else:
            df_visibles = proyectos_local[proyectos_local["proyectos"].isin(allowed)].copy()

        # ✅ EXCLUIR proyectos: 8002 (OFICINAS LUNA), 8003 (PATIO), 8004 (OFICINAS ANDARES)
        excluir = {"8002", "8003", "8004"}
        df_visibles = df_visibles[~df_visibles["proyectos"].astype(str).isin(excluir)].copy()

        nombres = df_visibles["nombre"].tolist()
        codigos = df_visibles["proyectos"].tolist()
        real_pct = {}

        for nombre, codigo in zip(nombres, codigos):
            codigo_list = [str(codigo)]

            er_real = estado_resultado(
                df_real,
                meses_sel,
                nombre,
                codigo_list,
                list_pro
            )

            real_pct[nombre] = float(er_real.get("por_utilidad_operativa", 0) or 0)

        ppt_pct = {n: objetivo_uo.get(n, 0) for n in nombres}

        tabla_excel = pd.DataFrame(
            {n: [ppt_pct.get(n, 0), real_pct.get(n, 0)] for n in nombres},
            index=["PPT", "REAL"]
        )

        st.markdown("Utilidad Operativa")
        st.dataframe(
            tabla_excel.style.format("{:.2%}"),
            use_container_width=True
        )

        fig = go.Figure()

        fig.add_bar(
            x=nombres,
            y=[ppt_pct[n] for n in nombres],
            name="PPT",
            text=[f"{ppt_pct[n]*100:.2f}%" for n in nombres],
            textposition="inside"
        )

        fig.add_bar(
            x=nombres,
            y=[real_pct[n] for n in nombres],
            name="REAL",
            text=[f"{real_pct[n]*100:.2f}%" for n in nombres],
            textposition="inside"
        )

        fig.update_layout(
            title=f"% Utilidad Operativa",
            xaxis_title="Proyecto",
            yaxis_title="Porcentaje",
            barmode="group",
            height=520,
            hovermode="x unified",
            xaxis_tickformat=".0%",
            xaxis_tickangle=-25
        )

        st.markdown("Utilidad Operativa")
        st.plotly_chart(fig, use_container_width=True)





