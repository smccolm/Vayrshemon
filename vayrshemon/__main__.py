"""Desktop, headless rendering, diagnostics, live API and stdio MCP entry point."""
import argparse
import json
import os
from pathlib import Path
import sys
import traceback


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    sub = parser.add_subparsers(dest='command', required=True)
    lab = sub.add_parser('lab')
    lab.add_argument('--document', type=Path)
    lab.add_argument('--no-source-fonts', action='store_true')
    editor = sub.add_parser('editor')
    editor.add_argument('--document',type=Path)
    editor.add_argument('--no-source-fonts',action='store_true')
    editor.add_argument('--m2',action='store_true',help='Open the frozen M2 authoring interface.')
    editor.add_argument('--m3',action='store_true',help='Open the frozen M3 typesetting interface.')
    editor.add_argument('--m4',action='store_true',help='Open the M4 glyph studio without language data.')
    editor.add_argument('--m5',action='store_true',help='Open the frozen M5 language workbench.')
    editor.add_argument('--m6',action='store_true',help='Open the frozen M6.1 workbench.')
    editor.add_argument('--m7',action='store_true',help='Open the M7 Forge interface without the M8 laboratory.')
    editor.add_argument('--m8',action='store_true',help='Open the frozen M8 laboratory interface.')
    editor.add_argument('--forge-project',type=Path,help='Open an independent M7 Forge project beside the document.')
    editor.add_argument('--page-focus',action='store_true',help='Open with a larger clean page preview; View restores editing and diagnostics.')
    for name in ('inspect', 'render', 'benchmark'):
        p = sub.add_parser(name)
        p.add_argument('--document', type=Path)
        p.add_argument('--no-source-fonts', action='store_true')
        p.add_argument('--out', type=Path)
        if name == 'render':
            p.add_argument('--mode', choices=['mono','color'], default='color')
            p.add_argument('--dpi', type=float, default=96)
            p.add_argument('--region', type=float, nargs=4)
    mcp = sub.add_parser('mcp')
    mcp.add_argument('--headless', action='store_true')
    mcp.add_argument('--no-source-fonts', action='store_true')
    mcp.add_argument('--descriptor', type=Path)
    mcp.add_argument('--document', type=Path)
    mcp.add_argument('--editor',action='store_true',help='Use the M2 editor in headless mode; live MCP discovers the active API.')
    mcp.add_argument('--typesetter',action='store_true',help='Use M3 typesetting in headless mode.')
    mcp.add_argument('--studio',action='store_true',help='Use M4 paint/publication in headless mode.')
    mcp.add_argument('--language',action='store_true',help='Use the M5 language workbench in headless mode.')
    mcp.add_argument('--reliability',action='store_true',help='Use M6 reliability and background proofs in headless mode.')
    mcp.add_argument('--forge',action='store_true',help='Use M7 Language Forge in headless mode.')
    mcp.add_argument('--laboratory',action='store_true',help='Use M8 executable language tests in headless mode.')
    mcp.add_argument('--integration',action='store_true',help='Use M9 merges and releases in headless mode.')
    call = sub.add_parser('call')
    call.add_argument('method')
    arguments = call.add_mutually_exclusive_group()
    arguments.add_argument('--params', default='{}')
    arguments.add_argument('--params-file', type=Path)
    call.add_argument('--expected-revision', type=int)
    call.add_argument('--idempotency-key')
    call.add_argument('--document-id')
    call.add_argument('--descriptor', type=Path)
    args = parser.parse_args()
    if args.command == 'call':
        from .api import remote_call
        from tools.m0.common import load_json
        params = load_json(args.params_file) if args.params_file else json.loads(args.params)
        result = remote_call(args.root, args.method, params, expected_revision=args.expected_revision,
                             idempotency_key=args.idempotency_key, descriptor=args.descriptor, document_id=args.document_id)
        print(json.dumps(result, ensure_ascii=True, indent=2))
        return 0 if result['ok'] else 1
    if args.command == 'mcp' and not args.headless:
        from .mcp import serve
        from tools.m0.common import load_json
        info=load_json(args.descriptor or args.root/'.local/run/active.json')
        from .editor_api import METHODS as EDITOR_METHODS
        from .typesetting_api import METHODS as TYPESETTING_METHODS
        from .studio_api import METHODS as STUDIO_METHODS
        from .language_api import METHODS as LANGUAGE_METHODS
        from .reliability_api import METHODS as RELIABILITY_METHODS
        from .forge_api import METHODS as FORGE_METHODS
        from .laboratory_api import METHODS as LABORATORY_METHODS
        from .integration_api import METHODS as INTEGRATION_METHODS
        reliability_methods=RELIABILITY_METHODS
        if info['apiVersion']=='0.7.0':
            reliability_methods={k:v for k,v in RELIABILITY_METHODS.items() if not k.startswith('ui.sidebar')}
        serve(args.root, descriptor=args.descriptor,methods=INTEGRATION_METHODS if info['apiVersion']=='0.10.0' else LABORATORY_METHODS if info['apiVersion']=='0.9.0' else FORGE_METHODS if info['apiVersion']=='0.8.0' else reliability_methods if info['apiVersion'] in ('0.7.0','0.7.1') else LANGUAGE_METHODS if info['apiVersion']=='0.6.0' else STUDIO_METHODS if info['apiVersion']=='0.5.0' else TYPESETTING_METHODS if info['apiVersion']=='0.4.0' else EDITOR_METHODS if info['apiVersion']=='0.3.0' else None)
        return 0
    # Windows' offscreen plugin uses a dummy font backend. Hidden native Qt
    # supplies the same fonts and geometry as the window; Linux uses offscreen.
    if os.name != 'nt' and args.command not in ('lab','editor'):
        os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import qInstallMessageHandler
    from .session import Session
    from .api import API, LocalServer
    from . import layout
    from tools.m0.common import write_json
    app = QApplication.instance() or QApplication([])
    app.setApplicationName('Vayrshemon')
    use_integration=(args.command=='editor' and not any((args.m2,args.m3,args.m4,args.m5,args.m6,args.m7,args.m8))) or (args.command=='mcp' and args.integration)
    use_laboratory=use_integration or (args.command=='editor' and not any((args.m2,args.m3,args.m4,args.m5,args.m6,args.m7))) or (args.command=='mcp' and args.laboratory)
    use_forge=use_laboratory or (args.command=='editor' and not any((args.m2,args.m3,args.m4,args.m5,args.m6))) or (args.command=='mcp' and args.forge)
    use_reliability=use_forge or (args.command=='editor' and not any((args.m2,args.m3,args.m4,args.m5))) or (args.command=='mcp' and args.reliability)
    use_language=use_reliability or (args.command=='editor' and not args.m2 and not args.m3 and not args.m4) or (args.command=='mcp' and args.language)
    use_studio=use_language or (args.command=='editor' and not args.m2 and not args.m3) or (args.command=='mcp' and args.studio)
    use_typesetter=use_studio or (args.command=='editor' and not args.m2) or (args.command=='mcp' and args.typesetter)
    use_editor=use_typesetter or args.command=='editor' or (args.command=='mcp' and args.editor)
    if getattr(args,'document',None) and args.command in ('inspect','render','mcp'):
        from tools.m0.common import load_json
        payload=load_json(args.document)
        use_editor=use_editor or payload.get('format')=='vayrshemon.document'
        use_typesetter=use_typesetter or (payload.get('format')=='vayrshemon.document' and payload.get('formatVersion')=='0.3.0')
        use_studio=use_studio or (payload.get('format')=='vayrshemon.document' and payload.get('formatVersion')=='0.4.0')
        use_language=use_language or (payload.get('format')=='vayrshemon.document' and payload.get('formatVersion')=='0.5.0')
        if args.command in ('inspect','render') and use_language: use_reliability=True
        use_studio=use_studio or use_language
        use_typesetter=use_typesetter or use_studio
    if use_editor:
        from .authoring import AuthoringSession
        from .editor_api import EditorAPI
        from .typesetting_session import TypesettingSession
        from .typesetting_api import TypesettingAPI
        from .studio_session import StudioSession
        from .studio_api import StudioAPI
        from .language_session import LanguageSession
        from .language_api import LanguageAPI
        from .reliability_session import ReliabilitySession
        from .reliability_api import ReliabilityAPI
        from .forge_api import ForgeSession,ForgeAPI
        from .laboratory_api import LaboratorySession,LaboratoryAPI
        from .integration_api import IntegrationSession,IntegrationAPI
        session=(IntegrationSession if use_integration else LaboratorySession if use_laboratory else ForgeSession if use_forge else ReliabilitySession if use_reliability else LanguageSession if use_language else StudioSession if use_studio else TypesettingSession if use_typesetter else AuthoringSession)(args.root,source_fonts=not args.no_source_fonts,recovery=args.command in ('editor','mcp'))
        api=(IntegrationAPI if use_integration else LaboratoryAPI if use_laboratory else ForgeAPI if use_forge else ReliabilityAPI if use_reliability else LanguageAPI if use_language else StudioAPI if use_studio else TypesettingAPI if use_typesetter else EditorAPI)(session)
    else:
        session = Session(args.root, source_fonts=not args.no_source_fonts)
        api = API(session)
    qInstallMessageHandler(lambda kind, context, message: session.log.emit('qt', str(kind), message=message))
    sys.excepthook = lambda kind, error, tb: session.log.emit('runtime', 'UNCAUGHT_EXCEPTION', level='error',
                                                             message=str(error), traceback=''.join(traceback.format_exception(kind,error,tb)))
    if getattr(args, 'document', None):
        session.open(args.document,advance_revision=False) if use_editor else session.open(args.document)
    if args.command=='editor':
        from .editor_window import EditorWindow
        from .workbench_window import WorkbenchWindow
        from .studio_window import StudioWindow
        from .language_window import LanguageWindow
        from .reliability_window import ReliabilityWindow
        from .forge_window import ForgeWindow
        from .laboratory_window import LaboratoryWindow
        if args.forge_project:
            if not use_forge: parser.error('--forge-project requires the M7 editor')
            from .forge import ForgeProject
            session.forge=ForgeProject(args.forge_project)
        from .integration_window import IntegrationWindow
        window=(IntegrationWindow if use_integration else LaboratoryWindow if use_laboratory else ForgeWindow if use_forge else ReliabilityWindow if use_reliability else LanguageWindow if use_language else StudioWindow if use_studio else WorkbenchWindow if use_typesetter else EditorWindow)(session,api)
        server=LocalServer(api)
        app.aboutToQuit.connect(server.close)
        window.show()
        if use_studio and args.page_focus:
            api.call('ui.workspace',dict(source=False,diagnostics=False,guides=False,fit_page=True,panel='Paint'),expected_revision=session.revision,origin='desktop')
        return app.exec()
    if args.command == 'lab':
        from .desktop import LabWindow
        window = LabWindow(session, api)
        server = LocalServer(api)
        app.aboutToQuit.connect(server.close)
        window.show()
        return app.exec()
    if args.command == 'mcp':
        from .mcp import serve
        serve(args.root, api)
        return 0
    if args.command == 'render':
        if not args.out:
            parser.error('render requires --out')
        if use_editor:
            from . import pages
            result=pages.render(session,args.out,mode=args.mode,dpi=args.dpi,region=args.region)[1]
        else: result = layout.render(session, args.out, mode=args.mode, dpi=args.dpi, region=args.region)[1]
    elif args.command == 'benchmark':
        from .benchmark import benchmark
        result = benchmark(session)
    else:
        if use_editor:
            from . import pages
            result=pages.inspect(session)
        else: result = layout.inspect(session)
    if args.out and args.command != 'render':
        path = session.output_path(args.out)
        if path.exists():
            raise ValueError('OUTPUT_EXISTS')
        write_json(path, result)
        print(json.dumps(dict(ok=True, path=str(path)), ensure_ascii=True))
        return 0
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception:
        traceback.print_exc(file=sys.stderr)
        raise SystemExit(1)
