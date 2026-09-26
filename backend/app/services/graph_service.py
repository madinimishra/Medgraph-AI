from sqlalchemy.orm import Session

from app.graph.graph_builder import GraphBuilder


class GraphService:

    @staticmethod
    def sync_graph(db: Session):

        GraphBuilder.build_graph(db)

        return {
            "message": "Knowledge Graph Synced Successfully"
        }