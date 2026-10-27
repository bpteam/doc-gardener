import importlib.util
import json
from collections import Counter
import subprocess
import tempfile
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / 'skills' / 'doc-gardener' / 'scripts' / 'docgraph.py'
SPEC = importlib.util.spec_from_file_location('docgraph', SRC)
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


class TestDocGraph(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        self.addCleanup(self.t.cleanup)
        self.root = Path(self.t.name)
        (self.root / 'docs').mkdir()

    def add(self, name, data):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(data, encoding='utf-8')
        return path

    def run_check(self, **opts):
        return mod.build(self.root, [], mod.config(self.root), **opts)

    def test_file_links(self):
        self.add('docs/INDEX.md', '# Index\n[topic](topic.md)\n')
        self.add('docs/topic.md', '# Topic\n')
        report = self.run_check()
        self.assertEqual(report['errors'], [])
        self.assertEqual(report['backlinks']['docs/topic.md'], ['docs/INDEX.md'])

    def test_broken_links(self):
        self.add('docs/index.md', '# Index\n[bad](missing.md)\n')
        report = self.run_check()
        self.assertEqual(report['errors'][0]['type'], 'broken_link')
        self.assertEqual(report['errors'][0]['line'], 2)

    def test_anchor_success_and_failure(self):
        self.add('docs/index.md', '# Index\n[A](a.md#my-heading)\n[B](a.md#gone)\n[This](#index)\n')
        self.add('docs/a.md', '# My Heading\n')
        r = self.run_check()
        self.assertEqual([v['type'] for v in r['errors']], ['broken_anchor'])

    def test_anchor_duplicates(self):
        self.add('docs/index.md', '# Index\n[A](a.md#heading-1)\n')
        self.add('docs/a.md', '# Heading\n## Heading\n')
        self.assertEqual(self.run_check()['errors'], [])

    def test_ignore_code_and_remote(self):
        self.add('docs/index.md', '# Index\n```md\n[bad](missing.md)\n```\n`[bad](missing.md)`\n[ok](https://example.org)\n<!-- [bad](not-real.md) -->\n')
        self.assertEqual(self.run_check()['errors'], [])

    def test_wiki_backlinks_order_independent(self):
        self.add('docs/index.md', '# Index\n[[topic]]\n')
        self.add('docs/topic.md', '# Topic\n')
        r = self.run_check()
        self.assertEqual(r['warnings'], [])
        self.assertEqual(r['backlinks']['docs/topic.md'], ['docs/index.md'])

    def test_ambiguous_wiki(self):
        self.add('docs/index.md', '# Index\n[[topic]]\n')
        self.add('docs/a/topic.md', '# Topic A\n')
        self.add('docs/b/topic.md', '# Topic B\n')
        self.assertEqual(self.run_check()['warnings'][0]['type'], 'ambiguous_wikilink')

    def test_orphan_and_reachability(self):
        self.add('docs/INDEX.md', '# Index\n[A](a.md)\n')
        self.add('docs/a.md', '# A\n')
        self.add('docs/hidden.md', '# Hidden\n')
        r = self.run_check(orphans=True)
        self.assertIn('orphan', {x['type'] for x in r['warnings']})
        self.assertIn('unreachable', {x['type'] for x in r['warnings']})

    def test_allow_orphans(self):
        self.add('docs/INDEX.md', '# Index\n')
        self.add('docs/archive/old.md', '# Old\n')
        self.add('.doc-gardener.json', json.dumps({'allow_orphans': ['docs/archive/**']}))
        self.assertFalse(self.run_check(orphans=True)['warnings'])

    def test_autodiscovers_other_existing_doc_roots(self):
        self.add('handbook/INDEX.md', '# Handbook\n[Page](page.md)\n')
        self.add('handbook/page.md', '# Page\n')
        self.add('modules/core/wiki/help.md', '# Help\n')
        r = self.run_check()
        self.assertEqual(r['pages_scanned'], 3)
        self.assertEqual(r['errors'], [])

    def test_config_includes_nested_glob(self):
        self.add('packages/core/doc/screen.md', '# Screen\n')
        self.add('.doc-gardener.json', json.dumps({'include': ['packages/*/doc']}))
        self.assertEqual(mod.build(self.root, [], mod.config(self.root))['pages_scanned'], 1)

    def test_duplicate_titles_and_bodies(self):
        self.add('docs/a.md', '# Same\nParagraph text.\n')
        self.add('docs/b.md', '# Same\nParagraph text.\n')
        r = self.run_check(duplicates=True)
        self.assertEqual({x['type'] for x in r['warnings']}, {'duplicate_title', 'exact_duplicate'})

    def test_reference_definition(self):
        self.add('docs/index.md', '# Index\n[ref]: other.md\n')
        self.add('docs/other.md', '# Other\n')
        r = self.run_check()
        self.assertEqual(r['backlinks']['docs/other.md'], ['docs/index.md'])

    def test_index_create_then_idempotent(self):
        self.add('docs/a.md', '# A\nHere is content about component A.\n')
        a = mod.make_index(self.root, 'docs', True)
        self.assertTrue(a['changed'])
        b = mod.make_index(self.root, 'docs', True)
        self.assertFalse(b['changed'])
        self.assertIn('[a](a.md)', (self.root / 'docs/INDEX.md').read_text())

    def test_index_refuses_nonmanaged(self):
        self.add('docs/INDEX.md', '# Manual index\n')
        with self.assertRaises(ValueError):
            mod.make_index(self.root, 'docs', True)

    def test_impact_mapping(self):
        subprocess.run(['git', '-C', str(self.root), 'init', '-q'], check=True)
        self.add('docs/INDEX.md', '# Index\n')
        self.add('backend/code.py', 'print(1)\n')
        self.add('.doc-gardener.json', json.dumps({'mappings': [{'code': 'backend/**', 'docs': ['docs/**']}]}))
        subprocess.run(['git', '-C', str(self.root), '-c', 'user.name=Test', '-c', 'user.email=t@example.org',
                        'add', '.'], check=True)
        subprocess.run(['git', '-C', str(self.root), '-c', 'user.name=Test', '-c', 'user.email=t@example.org',
                        'commit', '-qm', 'base'], check=True)
        self.add('backend/code.py', 'print(2)\n')
        r = mod.impact(self.root, 'HEAD', mod.config(self.root))
        self.assertIn('backend/code.py', r['code_changes'])
        self.assertEqual(r['documentation_candidates']['backend/code.py'], ['docs/**'])

    def test_outside_repo_safe(self):
        self.add('docs/index.md', '# Index\n[bad](../../secrets.md)\n')
        self.assertEqual(self.run_check()['warnings'][0]['type'], 'outside_repo')

    def test_cli_json_and_exit(self):
        self.add('docs/INDEX.md', '# Index\n[bad](gone.md)\n')
        cp = subprocess.run(['python3', str(SRC), 'check', '--root', str(self.root), '--json'],
                            capture_output=True, text=True)
        self.assertEqual(cp.returncode, 1)
        self.assertEqual(json.loads(cp.stdout)['errors'][0]['type'], 'broken_link')


class TestKnowledgeArchitecture(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        self.addCleanup(self.t.cleanup)
        self.root = Path(self.t.name)
        (self.root / 'docs' / 'concepts').mkdir(parents=True)

    def add(self, path, content):
        p = self.root / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding='utf-8')
        return p

    def concept(self, doc_id='example-topic', title='Example topic', relation=''):
        return (f'---\nid: {doc_id}\ntitle: {title}\nsummary: What this topic means.\n'
                f'kind: concept\nstatus: current\n---\n# {title}\n\nShort answer.\n'
                f'\n## Relationships\n{relation}\n')

    def test_structured_page_passes_policy(self):
        self.add('docs/INDEX.md', '# Docs\n[Topic](concepts/example-topic.md)\n')
        self.add('docs/concepts/example-topic.md', self.concept())
        report = mod.build(self.root, [], mod.config(self.root), policy=True)
        self.assertEqual(report['errors'], [])
        self.assertEqual(report['warnings'], [])

    def test_no_frontmatter_required_by_default_even_with_policy(self):
        self.add('docs/concepts/legacy.md', '# Legacy\nOld content.\n')
        report = mod.build(self.root, [], mod.config(self.root), policy=True)
        self.assertEqual(report['warnings'], [])

    def test_metadata_requirements_only_when_repo_opts_in(self):
        self.add('docs/concepts/legacy.md', '# Legacy\nOld content.\n')
        self.add('.doc-gardener.json', json.dumps({'metadata_profile': 'doc-gardener'}))
        report = mod.build(self.root, [], mod.config(self.root), policy=True)
        self.assertIn('missing_metadata', {x['type'] for x in report['warnings']})

    def test_policy_id_uniqueness(self):
        self.add('docs/concepts/example-topic.md', self.concept())
        self.add('docs/concepts/example-topic2.md', self.concept(title='Second title'))
        r = mod.build(self.root, [], mod.config(self.root), policy=True)
        self.assertIn('duplicate_doc_id', {i['type'] for i in r['warnings']})

    def test_invalid_kind_status_id_and_absent_relations(self):
        self.add('.doc-gardener.json', json.dumps({'metadata_profile': 'doc-gardener'}))
        text = self.concept(doc_id='Wrong ID', relation='')
        text = text.replace('kind: concept', 'kind: fabricated').replace('status: current', 'status: implemented')
        self.add('docs/concepts/wrong.md', text)
        kinds = {w['type'] for w in mod.build(self.root, [], mod.config(self.root), policy=True)['warnings']}
        self.assertEqual(kinds, {'invalid_doc_id', 'invalid_kind', 'invalid_status'})

    def test_typed_relationship_graph(self):
        self.add('docs/INDEX.md', '# Docs\n[Topic](concepts/example-topic.md)\n')
        self.add('docs/concepts/example-topic.md', self.concept(relation='- **Depends on:** [Other topic](other-topic.md)\n'))
        self.add('docs/concepts/other-topic.md', self.concept('other-topic', 'Other topic'))
        report = mod.build(self.root, [], mod.config(self.root), policy=True)
        self.assertEqual(report['relationships']['docs/concepts/example-topic.md']['depends_on'], ['docs/concepts/other-topic.md'])
        self.assertIn('docs/concepts/example-topic.md', report['backlinks']['docs/concepts/other-topic.md'])

    def test_index_only_flagged_with_automatic_orphans(self):
        self.add('docs/INDEX.md', '# Docs\n[Topic](concepts/example-topic.md)\n')
        self.add('docs/concepts/example-topic.md', self.concept())
        self.add('.doc-gardener.json', json.dumps({'metadata_profile': 'doc-gardener'}))
        report = mod.build(self.root, [], mod.config(self.root), orphans=True, policy=True)
        self.assertIn('index_only', {i['type'] for i in report['warnings']})
        self.assertNotIn('orphan', {i['type'] for i in report['warnings']})

    def test_policy_exclude_legacy_file(self):
        self.add('docs/concepts/legacy.md', '# Legacy\n')
        self.add('.doc-gardener.json', json.dumps({'policy_exclude': ['docs/concepts/legacy.md']}))
        report = mod.build(self.root, [], mod.config(self.root), policy=True)
        self.assertEqual(report['warnings'], [])

    def test_index_uses_summary_from_frontmatter(self):
        self.add('docs/concepts/example-topic.md', self.concept())
        self.assertIn('What this topic means.', mod.make_index(self.root, 'docs', False)['preview'])

    def test_missing_configured_entrypoint_flagged(self):
        self.add('docs/concepts/example-topic.md', self.concept())
        self.add('.doc-gardener.json', json.dumps({'entrypoints': ['docs/INDEX.md']}))
        warnings = mod.build(self.root, [], mod.config(self.root))['warnings']
        self.assertIn('missing_entrypoint', {w['type'] for w in warnings})

    def test_cli_policy_returns_warnings_but_passes_non_strict(self):
        self.add('docs/concepts/legacy.md', '# Legacy\n')
        self.add('.doc-gardener.json', json.dumps({'metadata_profile': 'doc-gardener'}))
        cmd = ['python3', str(SRC), 'check', '--root', str(self.root), '--policy', '--json']
        result = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertGreater(len(json.loads(result.stdout)['warnings']), 0)
        strict = subprocess.run(cmd[:-1] + ['--strict'], capture_output=True, text=True)
        self.assertEqual(strict.returncode, 1)


def git(root, *args):
    subprocess.run(['git', '-C', str(root), '-c', 'user.name=Test', '-c', 'user.email=t@example.org', *args],
                   check=True, capture_output=True)


class TestParsingFixes(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        self.addCleanup(self.t.cleanup)
        self.root = Path(self.t.name)

    def add(self, name, data):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(data, encoding='utf-8')
        return path

    def check(self, **opts):
        return mod.build(self.root, [], mod.config(self.root), **opts)

    def test_underscore_anchor_kept_like_github(self):
        self.add('docs/a.md', '# A\n## foo_bar\n## __init__ hooks\n')
        self.add('README.md', '[x](docs/a.md#foo_bar) [y](docs/a.md#init-hooks)\n')
        self.assertEqual(self.check()['errors'], [])

    def test_setext_and_html_anchors(self):
        self.add('docs/a.md', 'Title\n=====\n\nSub part\n--------\n<a id="Custom-Id"></a>\n<h3 name="legacy">L</h3>\n')
        self.add('README.md', '[a](docs/a.md#title) [b](docs/a.md#sub-part) [c](docs/a.md#Custom-Id) [d](docs/a.md#legacy)\n')
        self.assertEqual(self.check()['errors'], [])

    def test_obsidian_block_and_heading_text_anchors(self):
        self.add('docs/a.md', '# A\n## My Heading\nStep one ^step-01\n[[a#^step-01]] [[a#My Heading]] [[a#^gone]]\n')
        kinds = [w['type'] for w in self.check()['warnings']]
        self.assertEqual(kinds, ['unresolved_wiki_anchor'])

    def test_extensionless_page_links(self):
        self.add('docs/guide.md', '# Guide\n## Step\n')
        self.add('README.md', '[g](docs/guide) [s](docs/guide#step) [bad](docs/nope)\n')
        r = self.check()
        self.assertEqual([e['message'] for e in r['errors']], ['docs/nope'])
        self.assertEqual(r['backlinks']['docs/guide.md'], ['README.md'])
        mod.move(self.root, [('docs/guide.md', 'docs/kb/guide.md')], True)
        self.assertIn('[g](docs/kb/guide) [s](docs/kb/guide#step)', (self.root / 'README.md').read_text())

    def test_frontmatter_is_not_a_setext_heading(self):
        self.add('docs/a.md', '---\ntitle: x\n---\n# Real\n')
        self.add('README.md', '[a](docs/a.md#title-x)\n')
        self.assertEqual(self.check()['errors'][0]['type'], 'broken_anchor')

    def test_docs_beside_code_are_discovered(self):
        self.add('README.md', '# Root\n[core](packages/core/README.md)\n')
        self.add('packages/core/README.md', '# Core\n')
        self.add('src/api/NOTES.md', '# Notes\n')
        r = self.check(orphans=True)
        self.assertEqual(r['pages_scanned'], 3)
        self.assertEqual(r['backlinks']['packages/core/README.md'], ['README.md'])

    def test_skips_nested_repositories_and_gitignored(self):
        git(self.root, 'init', '-q')
        self.add('.gitignore', 'ignored/\n')
        self.add('README.md', '# Root\n')
        self.add('ignored/x.md', '[bad](nope.md)\n')
        self.add('wt/.git', 'gitdir: elsewhere\n')
        self.add('wt/y.md', '[bad](nope.md)\n')
        r = self.check()
        self.assertEqual(r['pages_scanned'], 1)
        self.assertEqual(r['errors'], [])

    def test_standalone_pages_not_orphans(self):
        self.add('README.md', '# Root\n')
        self.add('CHANGELOG.md', '# Changes\n')
        self.add('.github/ISSUE_TEMPLATE/bug.md', '# Bug\n')
        self.assertEqual(self.check(orphans=True)['warnings'], [])

    def test_code_refs_valid_stale_and_package_relative(self):
        self.add('src/auth/session.py', 'x = 1\n')
        self.add('packages/core/lib/x.ts', '')
        self.add('docs/auth.md', '# Auth\nSee `src/auth/session.py:12` and `src/auth/` and `src/gone.py`.\n'
                                 'Also [impl](../src/auth/session.py), `text/html`, `path/to/file.md`.\n')
        self.add('packages/core/docs/x.md', '# X\nCode in `lib/x.ts`.\n')
        r = self.check(code_refs=True)
        self.assertEqual(r['code_refs']['docs/auth.md'], ['src/auth', 'src/auth/session.py'])
        self.assertEqual(r['code_refs']['packages/core/docs/x.md'], ['packages/core/lib/x.ts'])
        stale = [w for w in r['warnings'] if w['type'] == 'stale_code_ref']
        self.assertEqual([w['target'] for w in stale], ['src/gone.py'])

    def test_section_and_near_duplicates(self):
        para = ' '.join(f'word{i}' for i in range(120))
        self.add('docs/a.md', f'# A\n## Setup\n{para}\n')
        self.add('docs/b.md', f'# B\n## Install\n{para}\n')
        self.add('docs/c.md', f'# C\n{para} extra tail words here\n')
        kinds = Counter(w['type'] for w in self.check(duplicates=True)['warnings'])
        self.assertEqual(kinds['duplicate_section'], 1)
        self.assertGreaterEqual(kinds['near_duplicate'], 2)


class TestWorkflowCommands(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        self.addCleanup(self.t.cleanup)
        self.root = Path(self.t.name)

    def add(self, name, data):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(data, encoding='utf-8')
        return path

    def read(self, name):
        return (self.root / name).read_text(encoding='utf-8')

    def test_impact_routes_by_references_without_mappings(self):
        git(self.root, 'init', '-q')
        self.add('src/auth/session.py', 'x = 1\n')
        self.add('docs/auth.md', '# Auth\nImplemented in `src/auth/session.py`.\n')
        self.add('docs/index.md', '# Index\n[auth](auth.md)\n')
        self.add('src/other.py', '')
        git(self.root, 'add', '.')
        git(self.root, 'commit', '-qm', 'base')
        self.add('src/auth/session.py', 'x = 2\n')
        self.add('src/other.py', 'y = 1\n')
        self.add('docs/auth.md', '# Auth\nImplemented in `src/auth/session.py`. Changed.\n')
        r = mod.impact(self.root, 'HEAD', {})
        self.assertEqual(r['referencing_docs'], {'src/auth/session.py': ['docs/auth.md']})
        self.assertEqual(r['unrouted_code_changes'], ['src/other.py'])
        self.assertEqual(r['docs_linking_to_changed_docs'], {'docs/auth.md': ['docs/index.md']})

    def test_check_changed_limits_scope(self):
        git(self.root, 'init', '-q')
        self.add('docs/old.md', '# Old\n[bad](missing.md)\n')
        self.add('docs/target.md', '# Target\n')
        self.add('docs/linker.md', '# L\n[t](target.md)\n')
        git(self.root, 'add', '.')
        git(self.root, 'commit', '-qm', 'base')
        (self.root / 'docs/target.md').unlink()
        self.add('docs/new.md', '# New\n[bad](also-missing.md)\n')
        r = mod.scope_to_changes(self.root, 'HEAD', {}, mod.build(self.root, [], {}))
        files = sorted(e['file'] for e in r['errors'])
        self.assertEqual(files, ['docs/linker.md', 'docs/new.md'])

    def test_route_ranks_title_and_sections(self):
        self.add('docs/payments/retries.md', '# Payment retries\nIntro.\n## Backoff\nRetries use exponential backoff.\n')
        self.add('docs/auth.md', '# Authentication\nNothing about money.\n')
        self.add('docs/misc.md', '# Misc\nA retry is mentioned once.\n')
        r = mod.route(self.root, 'how do payment retries work', {})
        self.assertEqual(r['results'][0]['path'], 'docs/payments/retries.md')
        self.assertNotIn('docs/auth.md', [x['path'] for x in r['results']])
        self.assertEqual(r['results'][0]['sections'][0]['heading'], 'Backoff')

    def test_route_cyrillic(self):
        self.add('docs/oplata.md', '# Оплата заказов\nПовторные платежи.\n')
        self.add('docs/other.md', '# Другое\n')
        r = mod.route(self.root, 'оплату заказа', {})
        self.assertEqual([x['path'] for x in r['results']], ['docs/oplata.md'])

    def test_scan_reports_conventions_questions_and_draft(self):
        self.add('README.md', '# Repo\n')
        self.add('mkdocs.yml', 'nav:\n  - guide/a.md\n')
        self.add('docs/index.md', '# Docs\n[a](guide/a.md)\n')
        self.add('docs/guide/a.md', '---\ntitle: A\n---\n# A\n')
        self.add('docs/api/generated/ref.md', '<!-- AUTO-GENERATED: do not edit -->\n# Ref\n')
        self.add('docs/archive/old.md', '# Old\n')
        self.add('packages/core/package.json', '{}')
        self.add('packages/core/README.md', '# Core\n')
        self.add('packages/web/package.json', '{}')
        self.add('tests/fixtures/broken.md', '[x](nope.md)\n')
        r = mod.scan(self.root, {})
        self.assertIn('mkdocs', r['renderers'])
        cfg = r['suggested_config']
        self.assertIn('docs/api/generated/**', cfg['exclude'])
        self.assertIn('tests/fixtures/**', cfg['exclude'])
        self.assertIn('docs/archive/**', cfg['allow_orphans'])
        self.assertIn('README.md', cfg['entrypoints'])
        self.assertIn({'code': 'packages/core/**', 'docs': ['packages/core/README.md']}, cfg['mappings'])
        ids = {q['id'] for q in r['questions']}
        self.assertTrue({'scope', 'renderer', 'generated', 'frontmatter', 'placement', 'activation'} <= ids)

    def test_init_writes_once(self):
        self.add('README.md', '# Repo\n')
        mod.init(self.root, {}, True, False)
        self.assertIn('entrypoints', json.loads(self.read('.doc-gardener.json')))
        with self.assertRaises(ValueError):
            mod.init(self.root, {}, True, False)

    def test_move_file_rewrites_inbound_and_outbound(self):
        self.add('README.md', '# R\n[a](docs/a.md#part) [abs](/docs/a.md) `docs/a.md`\n```\n[code](docs/a.md)\n```\n')
        self.add('docs/a.md', '# A\n## Part\n[b](b.md) [img](img/x.png) [self](#part) [[b]]\n')
        self.add('docs/b.md', '# B\n[back](./a.md "title")\n[ref]: a.md\n')
        self.add('docs/img/x.png', 'png')
        self.add('mkdocs.yml', 'nav:\n  - a.md\n  - docs/a.md\n')
        self.add('src/app.py', '# uses data.md and adocs/a.md, not ours\n')
        dry = mod.move(self.root, [('docs/a.md', 'docs/guides/alpha.md')], False)
        self.assertFalse(dry['applied'])
        self.assertTrue((self.root / 'docs/a.md').exists())
        r = mod.move(self.root, [('docs/a.md', 'docs/guides/alpha.md')], True)
        self.assertEqual(r['broken_after'], [])
        readme = self.read('README.md')
        self.assertIn('[a](docs/guides/alpha.md#part)', readme)
        self.assertIn('[abs](/docs/guides/alpha.md)', readme)
        self.assertIn('[code](docs/a.md)', readme)  # code blocks untouched
        alpha = self.read('docs/guides/alpha.md')
        self.assertIn('[b](../b.md)', alpha)
        self.assertIn('[img](../img/x.png)', alpha)
        self.assertIn('[self](#part)', alpha)
        b = self.read('docs/b.md')
        self.assertIn('[back](./guides/alpha.md "title")', b)
        self.assertIn('[ref]: guides/alpha.md', b)
        self.assertEqual({x['file'] for x in r['manual_followups']}, {'mkdocs.yml'})
        self.assertIn('`docs/guides/alpha.md`', readme)  # path mentions follow the move

    def test_move_directory_and_wikilink_rename(self):
        git(self.root, 'init', '-q')
        self.add('README.md', '# R\n[g](wiki/guide.md) [[old-name]]\n')
        self.add('wiki/guide.md', '# G\n[s](sub/s.md) [r](../README.md)\n')
        self.add('wiki/sub/s.md', '# S\n')
        self.add('notes/old-name.md', '# Old\n')
        git(self.root, 'add', '.')
        git(self.root, 'commit', '-qm', 'base')
        r = mod.move(self.root, [('wiki', 'docs/kb'), ('notes/old-name.md', 'docs/new-name.md')], True)
        self.assertEqual(r['broken_after'], [])
        self.assertFalse((self.root / 'wiki').exists())
        self.assertIn('[g](docs/kb/guide.md) [[new-name]]', self.read('README.md'))
        self.assertIn('[s](sub/s.md) [r](../../README.md)', self.read('docs/kb/guide.md'))
        status = subprocess.run(['git', '-C', str(self.root), 'status', '--porcelain'], capture_output=True, text=True).stdout
        self.assertIn('R  wiki/sub/s.md -> docs/kb/sub/s.md', status)

    def test_move_keeps_mentions_that_still_resolve(self):
        self.add('README.md', '# R\\n[s](SKILL.md) uses `scripts/tool.py`\\n')
        self.add('SKILL.md', '# S\\nRun `scripts/tool.py`; see [`references/a.md`](references/a.md).\\n')
        self.add('references/a.md', '# A\\nCall `scripts/tool.py`.\\n')
        self.add('scripts/tool.py', '')
        pairs = [('SKILL.md', 'pkg/SKILL.md'), ('references', 'pkg/references'), ('scripts', 'pkg/scripts')]
        r = mod.move(self.root, pairs, True)
        self.assertEqual(r['broken_after'], [])
        self.assertEqual(self.read('pkg/SKILL.md'), '# S\\nRun `scripts/tool.py`; see [`references/a.md`](references/a.md).\\n')
        self.assertEqual(self.read('pkg/references/a.md'), '# A\\nCall `scripts/tool.py`.\\n')
        self.assertIn('[s](pkg/SKILL.md) uses `pkg/scripts/tool.py`', self.read('README.md'))
        self.assertTrue(all(x['old'] != x['new'] for x in r['rewrites']))

    def test_move_refuses_overwrite_and_outside(self):
        self.add('docs/a.md', '# A\n')
        self.add('docs/b.md', '# B\n')
        with self.assertRaises(ValueError):
            mod.move(self.root, [('docs/a.md', 'docs/b.md')], True)
        with self.assertRaises(ValueError):
            mod.move(self.root, [('docs/a.md', '../escape.md')], True)

    def test_index_check_managed_and_manual(self):
        self.add('docs/a.md', '# A\nAbout component A in detail.\n')
        mod.make_index(self.root, 'docs', True)
        self.assertTrue(mod.make_index(self.root, 'docs', False, check=True)['ok'])
        self.add('docs/b.md', '# B\n')
        self.assertTrue(mod.make_index(self.root, 'docs', False, check=True)['stale'])
        self.add('guide/README.md', '# Guide\n[one](one.md)\n')
        self.add('guide/one.md', '# One\n')
        self.add('guide/two.md', '# Two\n')
        r = mod.make_index(self.root, 'guide', False, 'README.md', check=True)
        self.assertEqual(r['unlisted'], ['two.md'])

    def test_cli_route_and_scan_text(self):
        self.add('docs/a.md', '# Alpha topic\n')
        out = subprocess.run(['python3', str(SRC), 'route', '--root', str(self.root), 'alpha'],
                             capture_output=True, text=True)
        self.assertEqual(out.returncode, 0)
        self.assertIn('docs/a.md', out.stdout)
        out = subprocess.run(['python3', str(SRC), 'scan', '--root', str(self.root)], capture_output=True, text=True)
        self.assertEqual(out.returncode, 0)
        self.assertIn('Open questions', out.stdout)


if __name__ == '__main__':
    unittest.main()
