from pathlib import Path
from datetime import datetime, timezone
from hashlib import sha256
from collections import Counter
import json,sys
root=Path('/workspace/scratch/ccb7f80b4c57/EasyMusicRent');sys.path.insert(0,str(root/'scripts'))
import site_core as core
from source_policy import public_sources, source_class, PUBLIC_CLASSES, POLICY_PATH
output=root.parent/'dual-index-site'
pages=core.read_legacy(root,core.read_json(root/'content/legacy-metadata.json',{}));core.merge_records(root,pages)
for alias in core.read_json(root/'content/aliases.json',{}):pages.pop(alias,None)
def digest(value):return sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
before=digest({slug:page.sources for slug,page in sorted(pages.items())})
errors=[];counts=Counter();rows={}
def fail(slug,check,**details):errors.append({'slug':slug,'check':check,**details})
for i,(slug,page) in enumerate(sorted(pages.items()),1):
 expected=public_sources(page.sources);expected_pairs=[(s['url'],s['title']) for s in expected]
 n1=output/'details'/slug/'index.html';n0=output/slug/'index.html'
 if not n1.is_file():fail(slug,'missing_n1');continue
 if not n0.is_file():fail(slug,'missing_n0');continue
 deep=core.soup(n1.read_text(encoding='utf-8'));entry=core.soup(n0.read_text(encoding='utf-8'))
 blocks=deep.select('details.sources');entry_blocks=entry.select('.sources')
 counts['n1_checked']+=1;counts['n0_checked']+=1;counts['raw_source_occurrences']+=len(page.sources)
 counts['expected_public_source_occurrences']+=len(expected)
 if entry_blocks:fail(slug,'n0_has_sources',count=len(entry_blocks))
 if len(blocks)!=(1 if expected else 0):fail(slug,'n1_sources_block_count',expected=1 if expected else 0,actual=len(blocks))
 pairs=[]
 if blocks:
  counts['n1_with_documentation']+=1
  b=blocks[0];pairs=[(a.get('href'),a.get_text()) for a in b.select('a[href]')]
  counts['actual_public_source_occurrences']+=len(pairs)
  if pairs!=expected_pairs:fail(slug,'public_source_links_differ',expected=expected_pairs,actual=pairs)
  if b.has_attr('open'):fail(slug,'block_initially_open')
  summary=b.find('summary',recursive=False)
  if summary is None or summary.get_text(strip=True)!='Документация':fail(slug,'summary_text')
  tags=list(deep.find_all(True));positions={id(tag):idx for idx,tag in enumerate(tags)}
  footer=deep.select_one('.site-footer');contact=deep.select_one('.contact')
  if footer is None:fail(slug,'missing_footer')
  else:
   last=max(positions[id(footer)],*[positions[id(t)] for t in footer.find_all(True)])
   if positions[id(b)]<=last:fail(slug,'documentation_not_after_footer')
  wrap=deep.select_one('.page')
  if wrap is None or b.parent is not wrap:fail(slug,'documentation_not_direct_child_of_page')
  elif [x for x in wrap.children if getattr(x,'name',None)][-1] is not b:fail(slug,'documentation_not_last_page_element')
 else:counts['n1_without_documentation']+=1
 classes=Counter(source_class(s) for s in page.sources)
 rows[slug]={'url':core.DOMAIN+page.deep,'source_classes':dict(classes),'raw_sources':len(page.sources),'public_sources':len(expected)}
 if i%250==0:print(json.dumps({'checked':i,'errors':len(errors)},ensure_ascii=False),flush=True)
assert before==digest({slug:page.sources for slug,page in sorted(pages.items())})
candidates={
 'manufacturer_only':'yamaha-clp735-v-arendu',
 'mixed_public_and_hidden':'shure-sm58-v-arendu',
 'hidden_only':'weltmeister-perle-v-arendu',
 'museum':'klavikord',
 'exact_cdn':'gitarnyy-kabinet-1x12-dlya-pervogo-opyta'
}
examples={}
for key,slug in candidates.items():
 if slug not in rows:fail(slug,'missing_example');continue
 examples[key]={'slug':slug,**rows[slug],'public_links':public_sources(pages[slug].sources)}
report={
 'checked_at':datetime.now(timezone.utc).isoformat(timespec='seconds'),
 'status':'pass' if not errors else 'fail','scope':'All active N1 and N0 pages in built artifact; public sources and presentation placement.',
 'output':str(output),'counts':dict(counts),'errors':errors,
 'preservation':{'raw_page_sources_unchanged':True,'source_fields_sha256':before},
 'policy':{'path':str(POLICY_PATH),'sha256':sha256(POLICY_PATH.read_bytes()).hexdigest()},
 'checks':['exact authored href/title pairs equal public_sources in original order','absent block when no public sources','no sources block on N0','single closed block named Документация','block follows entire footer','block is last direct element of .page'],
 'examples':examples
}
out=root.parent/'dual-index-sources-artifact-audit.json';out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'report':str(out),'status':report['status'],'counts':dict(counts),'errors':errors,'examples':examples},ensure_ascii=False,indent=2),flush=True)
raise SystemExit(bool(errors))
