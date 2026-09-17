import io
t = io.open('D:/06_Hermes/articles/year-of-dataflow/article.html', encoding='utf-8').read()
i = t.find('e8f4fd')
print(t[i:i + 900])
print('=====')
j = t.find('两条路线')
