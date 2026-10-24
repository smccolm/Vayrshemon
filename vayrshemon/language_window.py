"""M5 language controls alongside the existing independent-column editor."""
from copy import deepcopy
import json
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QLabel,QLineEdit,QPlainTextEdit,QTextBrowser,QListWidget,QListWidgetItem,
    QDialog,QDialogButtonBox,QVBoxLayout,QFormLayout,QTabWidget,QFileDialog,QComboBox,QInputDialog,QPushButton,QSizePolicy)
from .studio_window import StudioWindow
from .language_contracts import COLLECTIONS, STATUS
from .authoring import identity
from . import language as lang
from .proof_names import suggested_proof_path


def pretty(value): return json.dumps(value,ensure_ascii=False,indent=2)


class LanguageWindow(StudioWindow):
    def __init__(self,book,api):
        self._language_ready=False
        super().__init__(book,api)
        for label in self.findChildren(QLabel):
            if label.text()=='GLYPH STUDIO  /  M4': label.setText('LANGUAGE WORKBENCH  /  M5')
        form=self.add_scroll_tab('Language')
        self.language_summary=QLabel();self.language_summary.setWordWrap(True);form.addRow(self.language_summary)
        self.note(form,'Each saved language edit creates a retained revision. Adopting a revision changes the language reference; page text and historical quotations keep their spelling.')
        self.revision_choice=QComboBox();form.addRow('Language revision',self.revision_choice)
        form.addRow(self.button('Compare with current revision',self.compare_revision))
        form.addRow(self.button('Adopt selected revision',lambda:self.invoke('language.adopt',revision_id=self.revision_choice.currentData())))
        form.addRow(self.button('Import verified local archive',lambda:self.invoke('language.archive.import')))
        form.addRow(self.button('Import language package…',self.import_language))
        form.addRow(self.button('Export language package…',self.export_language))
        self.note(form,'Both translation charts remain separate. “Attested” means present in that source; it does not mean the latest approved rule.')
        self.record_collection=self.combo(list(COLLECTIONS));form.addRow('Record collection',self.record_collection)
        form.addRow(self.button('Browse structured records…',self.browse_records))
        for kind in ('dictionary','grammar','corpus'):
            form.addRow(self.button('Publish '+{'dictionary':'dictionary','grammar':'grammar book','corpus':'interlinear corpus'}[kind]+'…',lambda k=kind:self.publish_language(k)))
        form=self.add_scroll_tab('Lexicon')
        self.lex_query=QLineEdit();self.lex_query.setPlaceholderText('English label, source spelling or definition');form.addRow('Search',self.lex_query)
        self.lex_query.returnPressed.connect(self.search_lexicon)
        form.addRow(self.button('Search dictionary',self.search_lexicon))
        self.lex_list=QListWidget();self.lex_list.setMinimumHeight(200);form.addRow(self.lex_list)
        self.lex_list.currentItemChanged.connect(lambda *_:self.lex_details())
        self.lex_list.itemDoubleClicked.connect(lambda *_:self.edit_selected_lexicon())
        self.lex_description=QTextBrowser();self.lex_description.setMinimumHeight(190);form.addRow(self.lex_description)
        form.addRow(self.button('Edit selected entry…',self.edit_selected_lexicon))
        form.addRow(self.button('New dictionary entry…',self.new_lexicon))
        form.addRow(self.button('Find linked occurrences',self.lex_occurrences))
        form=self.add_scroll_tab('Grammar')
        self.grammar_kind=self.combo(['grammar','morphology']);form.addRow('Collection',self.grammar_kind)
        self.grammar_list=QListWidget();self.grammar_list.setMinimumHeight(200);form.addRow(self.grammar_list)
        self.grammar_details=QPlainTextEdit();self.grammar_details.setReadOnly(True);self.grammar_details.setMinimumHeight(230);form.addRow(self.grammar_details)
        self.grammar_kind.currentTextChanged.connect(self.refresh_grammar)
        self.grammar_list.currentItemChanged.connect(lambda *_:self.show_grammar())
        form.addRow(self.button('Edit rule or paradigm…',self.edit_grammar))
        form.addRow(self.button('New rule or paradigm…',self.new_grammar))
        self.note(form,'Features and paradigm cells are explicit data. Competing analyses are retained; the workbench does not guess inflections from typography.')
        form=self.add_scroll_tab('Corpus')
        self.corpus_list=QListWidget();self.corpus_list.setMinimumHeight(120);form.addRow(self.corpus_list)
        self.corpus_detail=QTextBrowser();self.corpus_detail.setMinimumHeight(200);form.addRow(self.corpus_detail)
        self.corpus_list.currentItemChanged.connect(lambda *_:self.show_corpus())
        form.addRow(self.button('Edit interlinear analysis…',self.edit_corpus))
        form.addRow(self.button('Link this pair to document ranges…',self.link_pair))
        self.link_summary=QLabel();self.link_summary.setWordWrap(True);form.addRow(self.link_summary)
        form.addRow(self.button('Inspect document links',lambda:self.show_result('corpus.links')))
        form.addRow(self.button('Go to linked source',self.go_linked_source))
        self.corpus_query=QLineEdit();form.addRow('Concordance',self.corpus_query)
        form.addRow(self.button('Search corpus / count surface forms',lambda:self.show_result('corpus.search',query=self.corpus_query.text())))
        form=self.add_scroll_tab('Symbols')
        self.symbol_layout=QComboBox();form.addRow('Input layout',self.symbol_layout)
        self.symbol_keys=QListWidget();self.symbol_keys.setMinimumHeight(210);form.addRow(self.symbol_keys)
        self.symbol_layout.currentIndexChanged.connect(self.refresh_symbols)
        form.addRow(self.button('Insert selected symbol',self.insert_symbol))
        self.note(form,'Insertion uses the selected Text font and a verified compatible orthography. A semantic palette key is not a physical keyboard mapping.')
        self.trans_profile=QComboBox();form.addRow('Transliteration',self.trans_profile)
        self.trans_input=QPlainTextEdit();self.trans_input.setMaximumHeight(100);form.addRow('Source',self.trans_input)
        form.addRow(self.button('Transliterate with reversible trace',self.transliterate))
        self.trans_output=QPlainTextEdit();self.trans_output.setReadOnly(True);self.trans_output.setMaximumHeight(140);form.addRow(self.trans_output)
        form=self.add_scroll_tab('Numbers')
        self.number_convention=QComboBox();form.addRow('Reading convention',self.number_convention)
        self.numerator=QLineEdit('1');self.denominator=QLineEdit('7');form.addRow('Numerator',self.numerator);form.addRow('Denominator',self.denominator)
        form.addRow(self.button('Format exact base-12 value',self.format_number))
        self.number_text=QLineEdit();form.addRow('Base-12 notation',self.number_text)
        self.number_convention.currentIndexChanged.connect(self.sync_number_font)
        form.addRow(self.button('Parse to an exact fraction',self.parse_number))
        self.number_result=QPlainTextEdit();self.number_result.setReadOnly(True);self.number_result.setMinimumHeight(220);form.addRow(self.number_result)
        self.note(form,'Parentheses mark an exact repetend. An ellipsis means the display was shortened; the rational value stays exact. Unta positional spoken readings remain unverified.')
        menu=self.menuBar().addMenu('Language');self.language_menu=menu
        for name in ('Language','Lexicon','Grammar','Corpus','Symbols','Numbers'):
            menu.addAction(name).triggered.connect(lambda checked=False,n=name:self.invoke('ui.workspace',panel=n))
            panel=next(self.sidebar.widget(i) for i in range(self.sidebar.count()) if self.sidebar.tabText(i)==name)
            panel.widget().layout().setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
            for control in panel.findChildren(QComboBox):
                control.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
                control.setMinimumContentsLength(12);control.setMinimumWidth(0)
                control.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Fixed)
        self._language_ready=True;self._language_revision=None;self.refresh()

    def refresh(self):
        super().refresh()
        self.setWindowTitle(self.windowTitle().replace('M4','M5'))
        if not self._language_ready: return
        state=self.book.state['language'];rev=lang.revision(state)
        links=lang.inspect_links(self.book)
        self.link_summary.setText(f'{len(links)} document pairs · {sum(not x["valid"] for x in links)} stale · {sum(not x["usesActiveRevision"] for x in links)} pinned to earlier revisions')
        if self._language_revision==state['activeRevisionId']: return
        self._language_revision=state['activeRevisionId'];data=lang.dataset(state)
        self.language_summary.setText(f'{rev["label"]}\n{len(data["lexicon"])} entries · {len(data["grammar"])} grammar records · {len(data["corpus"])} corpus pairs\nRevision {rev["id"][-12:]}')
        self.revision_choice.blockSignals(True);self.revision_choice.clear()
        for r in reversed(state['revisions']): self.revision_choice.addItem(r['label']+' · '+r['id'][-8:],r['id'])
        self.revision_choice.setCurrentIndex(self.revision_choice.findData(state['activeRevisionId']));self.revision_choice.blockSignals(False)
        for widget,key in ((self.symbol_layout,'inputLayouts'),(self.trans_profile,'transliterations'),(self.number_convention,'numberConventions')):
            old=widget.currentData();widget.blockSignals(True);widget.clear()
            for r in data[key]: widget.addItem(r['label'],r['id'])
            if widget.findData(old)>=0: widget.setCurrentIndex(widget.findData(old))
            widget.blockSignals(False)
        self.search_lexicon();self.refresh_grammar();self.refresh_symbols()
        self.sync_number_font()
        self.fill_list(self.corpus_list,data['corpus'])

    def fill_list(self,widget,records):
        old=widget.currentItem().data(Qt.ItemDataRole.UserRole)['id'] if widget.currentItem() else None
        widget.blockSignals(True);widget.clear();selected=0
        for index,r in enumerate(records):
            item=QListWidgetItem(r['label']+' · '+r['status']);item.setData(Qt.ItemDataRole.UserRole,r);item.setToolTip(r['id']);widget.addItem(item)
            if r['id']==old: selected=index
        widget.blockSignals(False)
        if records: widget.setCurrentRow(selected)

    @staticmethod
    def chosen(widget):
        item=widget.currentItem()
        return deepcopy(item.data(Qt.ItemDataRole.UserRole)) if item else None

    def compare_revision(self):
        rid=self.revision_choice.currentData()
        if rid: self.show_result('language.diff',before=self.book.state['language']['activeRevisionId'],after=rid)

    def import_language(self):
        path,_=QFileDialog.getOpenFileName(self,'Import language revision',str(self.book.root/'.local'),'Language package (*.json)')
        if path: self.invoke('language.import',path=path)

    def export_language(self):
        path,_=QFileDialog.getSaveFileName(self,'Export language revision',suggested_proof_path(self.book,'language.json'),'Language package (*.json)')
        if path: self.show_result('language.export',path=path)

    def publish_language(self,kind):
        path,_=QFileDialog.getSaveFileName(self,'Publish '+kind,suggested_proof_path(self.book,kind+'.html'),'Printable HTML (*.html)')
        if path: self.show_result('language.publish',path=path,kind=kind)

    def search_lexicon(self):
        value=self.invoke('lexicon.search',query=self.lex_query.text(),limit=2000)
        if value: self.fill_list(self.lex_list,value['records'])
        if not self.lex_list.count(): self.lex_description.setPlainText('No matching entries. Import the local archive or create an entry.')

    def lex_details(self):
        r=self.chosen(self.lex_list)
        if r: self.lex_description.setPlainText('\n'.join([r['label'],r['headword'],r['pronunciation'],r['ipa'],r['partOfSpeech'],*['• '+s['definition'] for s in r['senses']],r.get('notes',''),*['Source: '+c['sourceId']+' · '+c['locator'] for c in r['citations']]]))

    def edit_selected_lexicon(self):
        r=self.chosen(self.lex_list)
        if r: self.edit_record('lexicon',r)

    def new_lexicon(self):
        rid=identity('entry')
        self.edit_record('lexicon',dict(id=rid,label='New entry',status='draft',citations=[],notes='',headword='',orthographyId=None,pronunciation='',ipa='',partOfSpeech='',senses=[dict(id=rid+'.sense1',definition='',status='draft',citations=[])],variants=[],etymology='',exampleIds=[],audioLinks=[]))

    def lex_occurrences(self):
        r=self.chosen(self.lex_list)
        if r: self.show_result('corpus.search',entry_id=r['id'])

    def refresh_grammar(self,*_):
        if not hasattr(self,'grammar_list'): return
        self.fill_list(self.grammar_list,lang.dataset(self.book.state['language'])[self.grammar_kind.currentText()])

    def show_grammar(self):
        r=self.chosen(self.grammar_list)
        self.grammar_details.setPlainText((r['label']+'\n'+r.get('statement',r.get('form',''))+'\n\n'+r.get('notes','')+'\n\n'+pretty(r.get('alternatives',r.get('cells',[])))) if r else '')

    def edit_grammar(self):
        r=self.chosen(self.grammar_list)
        if r: self.edit_record(self.grammar_kind.currentText(),r)

    def new_grammar(self):
        key=self.grammar_kind.currentText();r=dict(id=identity(key),label='New '+key,status='draft',citations=[],notes='')
        r.update(dict(topic='construction',statement='',morphologyIds=[],exampleIds=[],alternatives=[]) if key=='grammar' else dict(kind='paradigm',form='',features={},entryIds=[],cells=[]))
        self.edit_record(key,r)

    def show_corpus(self):
        from html import escape
        r=self.chosen(self.corpus_list)
        if not r: self.corpus_detail.clear();return
        body='<h3>'+escape(r['label'])+'</h3><p>'+escape(r['translation'])+'</p><table cellpadding="5"><tr><th>Token</th><th>Gloss</th></tr>'
        body+=''.join('<tr><td>'+escape(t['surface'])+'</td><td>'+escape(' · '.join(t['glosses']) or 'Unresolved')+'</td></tr>' for t in r['tokens'])+'</table>'
        self.corpus_detail.setHtml(body)

    def edit_corpus(self):
        r=self.chosen(self.corpus_list)
        if r: self.edit_record('corpus',r)

    def link_pair(self):
        r=self.chosen(self.corpus_list)
        if not r: return
        dialog=QDialog(self);dialog.setWindowTitle('Link a translation pair');dialog.resize(600,390);column=QVBoxLayout(dialog);form=QFormLayout();column.addLayout(form)
        form.addRow(QLabel('Choose exact UTF-16 ranges. This records alignment without moving or rewriting text.'))
        fields={}
        frames=[f for p in self.book.state['pages'] for f in p['frames']]
        for role in ('source','translation'):
            choice=QComboBox()
            for f in frames: choice.addItem(f['name'],f['frameId'])
            choice.setCurrentIndex(0 if role=='source' else min(1,len(frames)-1))
            start=self.spin('Start',0,0,400000,0);end=self.spin('End',0,0,400000,0)
            def fill(ch=choice,a=start,b=end,part=role):
                text=self.book.frames[ch.currentData()].text();needle=r['text' if part=='source' else 'translation'];pos=text.find(needle)
                a.setValue(lang.utf16_length(text[:pos]) if pos>=0 else 0);b.setValue(lang.utf16_length(text[:pos+len(needle)]) if pos>=0 else 0)
            choice.currentIndexChanged.connect(lambda _index,f=fill:f());fill()
            fields[role]=(choice,start,end);form.addRow(role.capitalize(),choice);form.addRow('Start / end',start);form.addRow('',end)
        note=QLineEdit();note.setPlaceholderText('Required when the document uses an adapted spelling');form.addRow('Adaptation',note)
        buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel);column.addWidget(buttons)
        buttons.rejected.connect(dialog.reject)
        def save():
            args={role:dict(frame_id=ch.currentData(),start=int(a.value()),end=int(b.value())) for role,(ch,a,b) in fields.items()}
            if self.invoke('corpus.link',corpus_id=r['id'],adaptation=note.text(),**args) is not None: dialog.accept()
        buttons.accepted.connect(save);dialog.exec()

    def go_linked_source(self):
        r=self.chosen(self.corpus_list)
        if not r: return
        link=next((l for l in lang.inspect_links(self.book) if l['corpusId']==r['id'] and l['valid']),None)
        if link:
            a=link['source'];self.invoke('ui.workspace',source=True);self.invoke('selection.set',frame_id=a['frameId'],start=a['start'],end=a['end'])

    def refresh_symbols(self,*_):
        if not hasattr(self,'symbol_keys'): return
        self.symbol_keys.clear();rid=self.symbol_layout.currentData()
        if not rid: return
        data=lang.dataset(self.book.state['language']);layout=lang.find_record(data,'inputLayouts',rid)
        orth=lang.find_record(data,'orthographies',layout['orthographyId'])
        names={f['scalar']:s['name']+' · '+f['form'] for s in orth['symbols'] for f in s['forms']}
        for key in layout['keys']:
            label=names.get(ord(key['text']),key['key']) if len(key['text'])==1 else key['key']
            item=QListWidgetItem(label);item.setToolTip(key['key']);item.setData(Qt.ItemDataRole.UserRole,key);self.symbol_keys.addItem(item)
        if self.symbol_keys.count(): self.symbol_keys.setCurrentRow(0)

    def insert_symbol(self):
        key=self.chosen(self.symbol_keys);fid=self.font_choice.currentData()
        if key and fid: self.invoke('orthography.input',layout_id=self.symbol_layout.currentData(),key=key['key'],font_id=fid,**self.selected_range())
        elif key: self.statusBar().showMessage('Choose a compatible loaded font in Text before inserting a symbol.',10000)

    def sync_number_font(self,*_):
        if not hasattr(self,'number_text'): return
        self.number_text.setStyleSheet('');self.number_text.setFont(self.font());self.number_text.setMinimumHeight(24)
        rid=self.number_convention.currentData()
        if not rid: return
        data=lang.dataset(self.book.state['language']);convention=lang.find_record(data,'numberConventions',rid)
        for orth in data['orthographies']:
            slots={chr(f['scalar']) for s in orth['symbols'] if s['kind']=='digit' for f in s['forms']}
            if set(convention['digits'])!=slots: continue
            candidates=[f for f in self.book.fonts.faces.values() if f.sha256 in orth['fontSha256s']]
            master=self.book.fonts.recipe['master'] if self.book.fonts.recipe else None
            candidates.sort(key=lambda f:f.font_id!=master)
            if candidates:
                font=QFont(candidates[0].family);font.setPointSizeF(30);self.number_text.setFont(font)
                # The editor's global QWidget stylesheet otherwise overrides
                # QFont and displays legacy slots as Latin letters.
                self.number_text.setStyleSheet(f'QLineEdit {{font-family:"{candidates[0].family}";font-size:30pt;}}')
                self.number_text.setMinimumHeight(72)
            break

    def transliterate(self):
        rid=self.trans_profile.currentData()
        if rid:
            value=self.invoke('orthography.transliterate',profile_id=rid,text=self.trans_input.toPlainText())
            if value: self.trans_output.setPlainText(value['text']+'\n\n'+str(len(value['diagnostics']))+' unresolved scalars preserved. Forward trace available through API / MCP.')

    def format_number(self):
        rid=self.number_convention.currentData()
        if rid:
            value=self.invoke('numbers.format',convention_id=rid,numerator=self.numerator.text(),denominator=self.denominator.text())
            if value: self.number_text.setText(value['text']);self.number_result.setPlainText(pretty(value))

    def parse_number(self):
        rid=self.number_convention.currentData()
        if rid:
            value=self.invoke('numbers.parse',convention_id=rid,text=self.number_text.text())
            if value: self.number_result.setPlainText(pretty(value))

    def browse_records(self):
        key=self.record_collection.currentText()
        dialog=QDialog(self);dialog.setWindowTitle('Browse '+key);dialog.resize(750,540);column=QVBoxLayout(dialog);listing=QListWidget();column.addWidget(listing)
        def reload(): self.fill_list(listing,lang.dataset(self.book.state['language'])[key])
        def edit():
            r=self.chosen(listing)
            if r: self.edit_record(key,r);reload()
        def add():
            self.edit_record(key,self.blank_record(key));reload()
        def remove():
            r=self.chosen(listing)
            if r: self.invoke('language.record.delete',collection=key,record_id=r['id']);reload()
        for label,action in [('New record…',add),('Edit selected…',edit),('Remove selected from new revision',remove)]:
            button=QPushButton(label);button.clicked.connect(action);column.addWidget(button)
        listing.itemDoubleClicked.connect(lambda *_:edit());reload();dialog.exec()

    def blank_record(self,key):
        from .language_contracts import RECORDS
        def default(schema):
            if 'const' in schema: return schema['const']
            if 'enum' in schema: return schema['enum'][0]
            kind=schema.get('type')
            if isinstance(kind,list): return None if 'null' in kind else ''
            if kind=='array': return []
            if kind=='object': return {k:default(schema['properties'][k]) for k in schema.get('required',[])}
            if kind in ('number','integer'): return schema.get('minimum',0)
            if kind=='boolean': return False
            return ''
        r=default(RECORDS[key]);r.update(id=identity(key),label='New '+key,status='draft',notes='')
        if key=='sources': r['sha256']='0'*64
        if key=='numberConventions': r.update(digits=list('0123456789AB'),digitNames=[str(n) for n in range(12)],radixPoint='.',minus='-',repeatOpen='(',repeatClose=')',readingPolicy='digits-only')
        if key in ('inputLayouts','transliterations'):
            orth=lang.dataset(self.book.state['language'])['orthographies']
            if orth: r['orthographyId']=orth[0]['id']
        return r

    def edit_record(self,collection,record):
        dialog=QDialog(self);dialog.setWindowTitle('Edit '+collection+' · '+record['id']);dialog.resize(800,700)
        column=QVBoxLayout(dialog);tabs=QTabWidget();column.addWidget(tabs)
        basic=QDialog();form=QFormLayout(basic);fields={}
        for key in ('label','headword','pronunciation','ipa','partOfSpeech','etymology','statement','notes'):
            if key not in record: continue
            widget=QPlainTextEdit(record[key]) if key in ('statement','notes','etymology') else QLineEdit(record[key])
            if isinstance(widget,QPlainTextEdit): widget.setMaximumHeight(100)
            fields[key]=widget;form.addRow({'partOfSpeech':'Part of speech','ipa':'IPA'}.get(key,key.capitalize()),widget)
        status=self.combo(STATUS['enum']);status.setCurrentText(record['status']);form.addRow('Status',status)
        definition=None
        if collection=='lexicon' and record['senses']:
            definition=QPlainTextEdit(record['senses'][0]['definition']);definition.setMaximumHeight(90);form.addRow('First sense',definition)
        form.addRow(QLabel('The structured tab edits citations, variants, sense IDs, paradigm cells and token links.'))
        tabs.addTab(basic,'Fields')
        raw=QPlainTextEdit(pretty(record));tabs.addTab(raw,'Structured record')
        current=[0]
        def sync(index):
            if current[0]==0:
                value=json.loads(raw.toPlainText())
                for k,w in fields.items(): value[k]=w.toPlainText() if isinstance(w,QPlainTextEdit) else w.text()
                value['status']=status.currentText()
                if definition is not None and value.get('senses'): value['senses'][0]['definition']=definition.toPlainText()
                raw.setPlainText(pretty(value))
            elif index==0:
                try: value=json.loads(raw.toPlainText())
                except ValueError: tabs.setCurrentIndex(1);return
                for k,w in fields.items(): (w.setPlainText if isinstance(w,QPlainTextEdit) else w.setText)(value.get(k,''))
                status.setCurrentText(value.get('status','draft'))
                if definition is not None: definition.setPlainText((value.get('senses') or [{}])[0].get('definition',''))
            current[0]=index
        tabs.currentChanged.connect(sync)
        error=QLabel();error.setWordWrap(True);column.addWidget(error)
        buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Save|QDialogButtonBox.StandardButton.Cancel);column.addWidget(buttons);buttons.rejected.connect(dialog.reject)
        def save():
            try:
                if tabs.currentIndex()==0:
                    current[0]=0;sync(1);current[0]=0
                value=json.loads(raw.toPlainText())
                if value['id']!=record['id']: raise ValueError('Keep the stable record ID; create a new record for a different identity.')
                result=self.invoke('language.record.put',collection=collection,record=value)
                if result is not None: dialog.accept()
            except (ValueError,KeyError,IndexError) as exc: error.setText(str(exc))
        buttons.accepted.connect(save);dialog.exec()
