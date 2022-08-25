import{_ as e,o,c as t,a}from"./app.84f6154f.js";const n={},s=a(`<h1 id="suffixes" tabindex="-1"><a class="header-anchor" href="#suffixes" aria-hidden="true">#</a> Suffixes</h1><p><code>pls</code> adds suffixes behind anything other than a regular UNIX file. This helps to identify the nature of the file and provide more information about it.</p><div style="background-color:#002b36;color:#839496;" class="language-"><pre style="color:inherit;"><code style="color:inherit;"><span style="color:#2aa198;text-decoration-color:#2aa198;">\uF07B</span>   <span style="color:#2aa198;text-decoration-color:#2aa198;">dir</span><span style="color:#156667;text-decoration-color:#156667;">/</span>                        
    fifo<span style="color:#415f66;text-decoration-color:#415f66;">|</span>                       
    file                        
    sock<span style="color:#415f66;text-decoration-color:#415f66;">=</span>                       
    sym_broken<span style="color:#415f66;text-decoration-color:#415f66;">@ \u2192</span> <span style="color:#dc322f;text-decoration-color:#dc322f;">none\u26A0</span>         
    sym_dir<span style="color:#415f66;text-decoration-color:#415f66;">@ \u2192</span> <span style="color:#2aa198;text-decoration-color:#2aa198;">dir</span><span style="color:#156667;text-decoration-color:#156667;">/</span>             
    sym_self<span style="color:#415f66;text-decoration-color:#415f66;">@ \u21BA</span> <span style="color:#dc322f;text-decoration-color:#dc322f;">sym_self</span>        
    sym_sym<span style="color:#415f66;text-decoration-color:#415f66;">@ \u2192</span> sym_dir<span style="color:#415f66;text-decoration-color:#415f66;">@ \u2192</span> <span style="color:#2aa198;text-decoration-color:#2aa198;">dir</span><span style="color:#156667;text-decoration-color:#156667;">/</span>  
</code></pre></div><h2 id="reference" tabindex="-1"><a class="header-anchor" href="#reference" aria-hidden="true">#</a> Reference</h2><p><code>pls</code> can identify and annotate the following file types.</p><table><thead><tr><th>Type</th><th>Suffix</th></tr></thead><tbody><tr><td>directory</td><td><code>/</code></td></tr><tr><td>named pipe / FIFO</td><td><code>|</code></td></tr><tr><td>socket</td><td><code>=</code></td></tr><tr><td>symlink</td><td><code>@</code></td></tr></tbody></table><p>Symlinks, being special, have additional information in the suffix.</p><ul><li>Normally symlinks have an arrow <code>\u2192</code> pointing to their destination node, as with <code>sym_dir</code> in the example above.</li><li>If their destination node is a symlink, it is suffixed in the same way, forming a chain, as with <code>sym_sym</code> in the example above.</li><li>If the destination node does not exist, the link is displayed in red with an error sign (<code>\u26A0</code>).</li><li>If the symlinks form a loop, the link is displayed in red and the arrow is replaced with the loop symbol (<code>\u21BA</code>).</li></ul>`,8),r=[s];function i(d,c){return o(),t("div",null,r)}var f=e(n,[["render",i],["__file","suffixes.html.vue"]]);export{f as default};
