window.__srSearch=function(kws,page,cmin,cmax){const x=new XMLHttpRequest();x.open('POST','/zf_user/memcom/talent-pool/get-condition-temp',false);x.setRequestHeader('X-Requested-With','XMLHttpRequest');x.send();
const c=JSON.parse(x.responseText).conditions;c.required.career_min=cmin||'3';c.required.career_max=cmax||'';c.hiring_spec_seq='';delete c.insert_dt;delete c.save_flag;
c.required.job_category=[];c.selective.school=[];c.selective.industry=[];c.selective.hire_company={company_nm:''};c.employed=[];c.res_item_tag=[];c.recent_com_scale=[];
c.search_keyword=kws.map(k=>({keyword:k[1],type:'18',search:k[0],match_type:'match'}));
const p=Object.assign({},c,{res_tag_cd:'',page:page,newbieFl:'',orderBy:'',lastUpdatePeriod:'',openFl:''});
const u=new URLSearchParams();for(const k in p){u.append(k,(typeof p[k]==='string'||typeof p[k]==='number')?p[k]:JSON.stringify(p[k]))}
const y=new XMLHttpRequest();y.open('POST','/zf_user/memcom/talent-pool/search-list',false);y.setRequestHeader('Content-Type','application/x-www-form-urlencoded');y.send(u.toString());return JSON.parse(y.responseText).data;};
